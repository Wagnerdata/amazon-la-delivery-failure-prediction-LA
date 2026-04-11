"""
agents_crew.py — Operational Analysis Agent Tools
Amazon LA Delivery Failure Prediction Project

Provides tool_operational_analysis for row-level package risk assessment.
"""

from __future__ import annotations
from typing import Any


def tool_operational_analysis(row: dict[str, Any]) -> dict[str, Any]:
    """
    Analyse a single delivery record and return operational flags and positives.

    Parameters
    ----------
    row : dict
        One row from packages_train / packages_validation / packages_test.

    Returns
    -------
    dict with keys:
        'flags'     — list of warning strings
        'positives' — list of positive-signal strings
        'summary'   — short overall assessment
    """
    flags: list[str] = []
    positives: list[str] = []

    # ── Operational error flags ──────────────────────────────────────────────
    if row.get("damaged_on_arrival") == 1:
        flags.append("CRITICAL: Delivery Failure Recorded (Damaged/Attempted)")

    if row.get("double_scan") == 1:
        flags.append("WARNING: Double scan detected — possible routing error")

    if row.get("locker_issue") == 1:
        flags.append("WARNING: Locker access issue reported")

    if row.get("cr_number_missing") == 1:
        flags.append("WARNING: Customer reference number missing — address ambiguity risk")

    # ── Carrier & route flags ────────────────────────────────────────────────
    if row.get("carrier") == "carrier_D":
        flags.append("WARNING: Carrier D (Correos) — baseline underperformance")
        route_km = row.get("route_distance_km", 0)
        if route_km > 50:
            flags.append(f"WARNING: Carrier D + long route ({route_km:.1f} km) — high SLA miss risk")

    if (row.get("package_type") == "high_value") and (row.get("shift") == "night"):
        flags.append("WARNING: High-value package on night shift — increased security risk")

    # ── Positive signals ─────────────────────────────────────────────────────
    if row.get("carrier") in ("carrier_A", "carrier_B"):
        positives.append("✅ Reliable carrier (A or B)")

    if row.get("damaged_on_arrival") == 0 and row.get("double_scan") == 0 and row.get("locker_issue") == 0:
        positives.append("✅ No operational errors detected")

    # ── Summary ──────────────────────────────────────────────────────────────
    critical = sum(1 for f in flags if f.startswith("CRITICAL"))
    warnings = sum(1 for f in flags if f.startswith(("WARNING", "⚠")))

    if critical > 0:
        summary = "CRITICAL — immediate intervention required"
    elif warnings >= 3:
        summary = "HIGH RISK — multiple risk factors active"
    elif warnings >= 1:
        summary = "MEDIUM RISK — review recommended"
    else:
        summary = "LOW RISK — standard delivery expected"

    return {
        "flags":     flags,
        "positives": positives,
        "summary":   summary,
    }


# ── Quick demo ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import pandas as pd
    from pathlib import Path

    DATA = Path(__file__).parent / "data"
    df = pd.read_csv(DATA / "packages_train.csv")

    print("=" * 60)
    print("  Operational Analysis — Sample Rows")
    print("=" * 60)

    for _, row in df.head(5).iterrows():
        result = tool_operational_analysis(row.to_dict())
        print(f"\nPackage : {row['package_id']}")
        print(f"Summary : {result['summary']}")
        for f in result['flags']:
            print(f"  {f}")
        for p in result['positives']:
            print(f"  {p}")
