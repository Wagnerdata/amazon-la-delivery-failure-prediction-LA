"""
build_dataset.py — Build packages_validation.csv from the real Amazon
Last Mile Routing Research Challenge dataset (ALMRRC 2021).

Source  : s3://amazon-last-mile-challenges  (public, no credentials needed)
Files used:
  - model_build_inputs/route_data.json      (~78 MB, streamed)
  - model_build_inputs/package_data.json    (~375 MB, first ~5 MB streamed)
  - model_build_inputs/actual_sequences.json (~10 MB, full download)

Run with:
    python data/build_dataset.py
"""

import os
import re
import json
import math
from datetime import datetime
from pathlib import Path

import boto3
import pandas as pd
from botocore import UNSIGNED
from botocore.client import Config


# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR  = Path(__file__).parent
CACHE_DIR = DATA_DIR / "raw" / "amazon_lmrc"
OUTPUT    = DATA_DIR / "packages_validation.csv"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

BUCKET = "amazon-last-mile-challenges"
PREFIX = "almrrc2021/almrrc2021-data-training/model_build_inputs/"

# Number of routes to extract (each route ≈ 600–900 packages → 15 routes ≈ 10k rows)
N_ROUTES = 15


# ── Haversine distance (km) ───────────────────────────────────────────────────
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance between two lat/lng points in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(max(0.0, a)))


# ── Streaming JSON extractor ──────────────────────────────────────────────────
def stream_extract_routes(s3, key: str, n_routes: int,
                          max_mb: int = 20) -> dict:
    """
    Download a large route-keyed JSON file in 512 KB chunks and extract the
    first n_routes complete route objects without loading the full file.

    Handles NaN literals (present in package time-window fields) by replacing
    them with null before parsing each chunk.
    """
    CHUNK = 512 * 1024          # 512 KB per request
    MAX   = max_mb * 1024 * 1024

    print(f"  Streaming s3://{BUCKET}/{key}  (max {max_mb} MB)…")

    buffer   = ""
    result   = {}
    byte_pos = 0

    while byte_pos < MAX and len(result) < n_routes:
        end_byte = min(byte_pos + CHUNK - 1, MAX - 1)
        resp   = s3.get_object(Bucket=BUCKET, Key=key,
                               Range=f"bytes={byte_pos}-{end_byte}")
        buffer += resp["Body"].read().decode("utf-8", errors="replace")
        byte_pos = end_byte + 1

        # Replace bare NaN with null so json.loads accepts the chunk
        buffer = re.sub(r":\s*NaN\b", ": null", buffer)

        # Locate every RouteID marker in the current buffer
        markers = [m.start() for m in
                   re.finditer(r'"RouteID_[a-f0-9\-]+":', buffer)]

        # Extract routes that are fully contained (i.e. not the trailing one)
        for i in range(len(markers) - 1):
            pos, nxt = markers[i], markers[i + 1]

            id_m = re.match(r'"(RouteID_[a-f0-9\-]+)":\s*', buffer[pos:])
            if not id_m:
                continue
            route_id = id_m.group(1)
            if route_id in result:
                continue

            # Isolate the route's key: value segment and close it as JSON
            segment  = buffer[pos:nxt].rstrip().rstrip(",").rstrip()
            json_str = "{" + segment + "}"

            try:
                result.update(json.loads(json_str))
            except json.JSONDecodeError:
                pass   # partial / malformed — skip

            if len(result) >= n_routes:
                break

        # Keep only from the last marker to avoid re-processing
        if markers:
            buffer = buffer[markers[-1]:]

    print(f"  → Extracted {len(result)} routes")
    return result


# ── Small file: full download with caching ────────────────────────────────────
def download_cached(s3, key: str, local_path: Path) -> None:
    """Download key to local_path unless the file is already cached."""
    if local_path.exists():
        print(f"  [cached] {local_path.name}")
        return
    print(f"  Downloading {key}…")
    s3.download_file(BUCKET, key, str(local_path))
    size_mb = local_path.stat().st_size / 1024 / 1024
    print(f"  → Saved {size_mb:.1f} MB to {local_path.name}")


# ── Feature derivations ───────────────────────────────────────────────────────
def departure_to_shift(dep_time: str) -> str:
    """
    Map UTC departure time to shift:
      06:00–14:00 → morning
      14:00–22:00 → afternoon
      22:00–06:00 → night
    """
    try:
        hour = int(dep_time[:2])
    except (ValueError, TypeError):
        return "morning"
    if 6 <= hour < 14:
        return "morning"
    elif 14 <= hour < 22:
        return "afternoon"
    else:
        return "night"


def station_to_carrier(station_code: str) -> str:
    """
    Derive carrier from the station code's 3-letter prefix:
      DLA* → carrier_A  (Amazon Logistics Area A)
      DBO* → carrier_B  (Operations Hub B)
      DSE* → carrier_C  (South-East hub)
      DCH* / others → carrier_D
    """
    prefix = station_code[:3].upper()
    mapping = {
        "DLA": "carrier_A",
        "DBO": "carrier_B",
        "DSE": "carrier_C",
        "DCH": "carrier_D",
    }
    return mapping.get(prefix, "carrier_D")


def date_to_weather(date_str: str) -> str:
    """
    Derive weather risk from the delivery month:
      Dec–Feb → high  (winter storms)
      Mar–May / Sep–Nov → medium  (spring/autumn variability)
      Jun–Aug → low   (summer)
    """
    try:
        month = int(date_str[5:7])
    except (ValueError, TypeError):
        return "medium"
    if month in (12, 1, 2):
        return "high"
    elif month in (6, 7, 8):
        return "low"
    else:
        return "medium"


def compute_route_distance(stops: dict, seq: dict) -> float:
    """
    Compute total route distance (km) via haversine between consecutive stops.
    Uses the actual delivery sequence when available; falls back to alphabetical
    stop order so every route always produces a positive distance.
    """
    if not stops:
        return 0.0

    # Order stops by their actual sequence position (if we have it)
    if seq:
        ordered = sorted(
            [(pos, sid) for sid, pos in seq.items() if sid in stops],
            key=lambda x: x[0],
        )
        stop_ids = [sid for _, sid in ordered]
    else:
        stop_ids = sorted(stops.keys())

    coords = [
        (stops[sid]["lat"], stops[sid]["lng"])
        for sid in stop_ids
        if sid in stops and "lat" in stops[sid] and "lng" in stops[sid]
    ]

    if len(coords) < 2:
        return 0.0

    return round(
        sum(haversine(coords[i][0], coords[i][1],
                      coords[i + 1][0], coords[i + 1][1])
            for i in range(len(coords) - 1)),
        2,
    )


# ── Main pipeline ─────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("  Amazon LMRC 2021 → packages_validation.csv")
    print("=" * 60)

    # S3 client with anonymous (unsigned) access — no credentials required
    s3 = boto3.client(
        "s3",
        region_name="us-east-1",
        config=Config(signature_version=UNSIGNED),
    )

    # ── Step 1: Fetch route metadata (streamed) ───────────────────────────────
    print(f"\n[1/4] Fetching route metadata (first {N_ROUTES} routes)…")

    route_cache = CACHE_DIR / "route_data_partial.json"
    if route_cache.exists():
        print(f"  [cached] {route_cache.name}")
        route_data = json.loads(route_cache.read_text(encoding="utf-8"))
    else:
        route_data = stream_extract_routes(
            s3, PREFIX + "route_data.json", N_ROUTES, max_mb=5
        )
        route_cache.write_text(json.dumps(route_data), encoding="utf-8")

    print(f"  Routes loaded: {len(route_data)}")

    # ── Step 2: Fetch package data (streamed) ────────────────────────────────
    print(f"\n[2/4] Streaming package data (first {N_ROUTES} routes)…")

    pkg_cache = CACHE_DIR / "package_data_partial.json"
    if pkg_cache.exists():
        print(f"  [cached] {pkg_cache.name}")
        pkg_data = json.loads(pkg_cache.read_text(encoding="utf-8"))
    else:
        pkg_data = stream_extract_routes(
            s3, PREFIX + "package_data.json", N_ROUTES, max_mb=20
        )
        pkg_cache.write_text(json.dumps(pkg_data), encoding="utf-8")

    print(f"  Package routes loaded: {len(pkg_data)}")

    # ── Step 3: Fetch actual sequences (small file, full download) ────────────
    print("\n[3/4] Fetching actual delivery sequences…")

    seq_cache = CACHE_DIR / "actual_sequences.json"
    download_cached(s3, PREFIX + "actual_sequences.json", seq_cache)
    sequences = json.loads(seq_cache.read_text(encoding="utf-8"))
    # Format: RouteID → {"actual": {stop_id: position_int}}

    # ── Step 4: Build the output DataFrame ────────────────────────────────────
    print("\n[4/4] Transforming to target schema…")

    # Group records by route for splitting
    route_records = {}

    for route_id, stop_pkgs in pkg_data.items():
        if route_id not in route_data:
            continue
        
        route_records[route_id] = []
        info      = route_data[route_id]
        station   = info.get("station_code", "DLA0")
        date_str  = info.get("date_YYYY_MM_DD", "2018-07-01")
        dep_time  = info.get("departure_time_utc", "08:00:00")
        stops_geo = info.get("stops", {})

        shift             = departure_to_shift(dep_time)
        carrier           = station_to_carrier(station)
        weather_risk      = date_to_weather(date_str)
        route_seq         = sequences.get(route_id, {}).get("actual", {})
        route_distance_km = compute_route_distance(stops_geo, route_seq)
        packages_in_route = sum(len(pkgs) for pkgs in stop_pkgs.values())

        pkg_stop_count: dict[str, int] = {}
        for pkgs in stop_pkgs.values():
            for pkg_id in pkgs:
                pkg_stop_count[pkg_id] = pkg_stop_count.get(pkg_id, 0) + 1

        dep_date = datetime.strptime(date_str, "%Y-%m-%d")

        for stop_id, pkgs in stop_pkgs.items():
            for pkg_id, pkg_info in pkgs.items():
                if not isinstance(pkg_info, dict):
                    continue

                dims   = pkg_info.get("dimensions") or {}
                d      = float(dims.get("depth_cm",  0) or 0)
                h      = float(dims.get("height_cm", 0) or 0)
                w      = float(dims.get("width_cm",  0) or 0)
                volume  = d * h * w
                max_dim = max(d, h, w)
                pkg_type = "high_value" if (volume > 8_000 or max_dim > 60) else "standard"

                tw       = pkg_info.get("time_window") or {}
                tw_start = tw.get("start_time_utc")
                days_in_fc = 0
                if tw_start and str(tw_start) not in ("None", "nan", ""):
                    try:
                        tw_date    = datetime.strptime(str(tw_start)[:10], "%Y-%m-%d")
                        days_in_fc = max(0, (dep_date - tw_date).days)
                    except ValueError:
                        days_in_fc = 0

                scan = (pkg_info.get("scan_status") or "DELIVERED").strip()
                failed = scan == "DELIVERY_ATTEMPTED"

                delivery_failed = 1 if failed else 0
                double_scan = 1 if pkg_stop_count.get(pkg_id, 1) > 1 else 0
                svc_sec      = float(pkg_info.get("planned_service_time_seconds") or 60)
                short_service_time = 1 if svc_sec < 25 else 0
                cr_number_missing = 1 if (
                    not tw_start or str(tw_start) in ("None", "nan", "")
                ) else 0

                route_records[route_id].append({
                    "package_id":        pkg_id,
                    "package_type":      pkg_type,
                    "shift":             shift,
                    "carrier":           carrier,
                    "route_distance_km": route_distance_km,
                    "packages_in_route": packages_in_route,
                    "weather_risk":      weather_risk,
                    "days_in_fc":        days_in_fc,
                    "double_scan":       double_scan,
                    "short_service_time": short_service_time,
                    "delivery_failed":   delivery_failed,
                    "cr_number_missing": cr_number_missing,
                })

    # Combine all records into one list for stratified split
    all_records = []
    for rid in route_records:
        all_records.extend(route_records[rid])
    
    if not all_records:
        raise RuntimeError("No records built.")

    df_full = pd.DataFrame(all_records)
    
    # Stratified split to ensure failure rate is preserved
    from sklearn.model_selection import train_test_split
    train_df, val_df = train_test_split(
        df_full, test_size=0.33, random_state=42,
        stratify=df_full["delivery_failed"]
    )

    COLS = [
        "package_id", "package_type", "shift", "carrier",
        "route_distance_km", "packages_in_route", "weather_risk",
        "days_in_fc", "double_scan", "short_service_time",
        "delivery_failed", "cr_number_missing",
    ]

    for df, filename in [(train_df, "packages_train.csv"),
                         (val_df, "packages_validation.csv")]:
        out_path = DATA_DIR / filename
        df[COLS].to_csv(out_path, index=False)
        rate = df["delivery_failed"].mean()
        print(f"  Saved {len(df):,} rows to {filename} | Failure rate: {rate:.2%}")


if __name__ == "__main__":
    main()
