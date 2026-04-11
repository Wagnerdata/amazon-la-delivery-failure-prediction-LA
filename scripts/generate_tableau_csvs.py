"""
generate_tableau_csvs.py
========================
Generates 7 Tableau-ready CSVs from packages_validation.csv and the
final SMOTE+RF model (ml/random_forest_model.pkl).

All GROUP BY tables use the same SQLite queries as sql/eda_queries.sql
so the numbers are guaranteed consistent with the EDA.

Output directory: reports/tableau/

CSV inventory:
  01_overall_summary.csv       — headline KPIs
  02_failure_by_carrier.csv    — carrier breakdown
  03_failure_by_shift.csv      — shift breakdown
  04_failure_by_package_type.csv — package type breakdown
  05_failure_by_distance.csv   — route distance bucket breakdown
  06_operational_flags.csv     — binary flag rates
  07_package_predictions.csv   — every package with model score + risk tier

Usage:
    python scripts/generate_tableau_csvs.py
"""

import pickle
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).parent.parent
CSV_PATH  = ROOT / "data"  / "packages_validation.csv"
MODEL_PATH = ROOT / "ml"   / "random_forest_model.pkl"
OUT_DIR   = ROOT / "reports" / "tableau"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Load data + model ──────────────────────────────────────────────────────────
print("Loading data and model…")
df = pd.read_csv(CSV_PATH)
df["delivery_failure"] = df["delivery_failed"]   # canonical target

with open(MODEL_PATH, "rb") as f:
    artifact = pickle.load(f)

model      = artifact["model"]
encoders   = artifact["encoders"]
features   = artifact["features"]
threshold  = artifact["best_threshold"]    # 0.05
metrics    = artifact["metrics"]

# ── Encode features for model scoring ─────────────────────────────────────────
df_enc = df.copy()
for col in ["carrier", "shift", "package_type"]:
    df_enc[col + "_enc"] = encoders[col].transform(df_enc[col])

df_enc["dist_bucket"] = pd.cut(
    df_enc["route_distance_km"],
    bins=[-1, 40, 60, 9_999],
    labels=[0, 1, 2],
).astype(int)

X      = df_enc[features].values
probs  = model.predict_proba(X)[:, 1]
preds  = (probs >= threshold).astype(int)

df["failure_prob"]    = probs.round(4)
df["predicted_risk"]  = preds
df["risk_tier"] = pd.cut(
    probs,
    bins=[-0.001, 0.05, 0.15, 0.40, 1.001],
    labels=["Low (<5%)", "Medium (5–15%)", "High (15–40%)", "Critical (>40%)"],
)

# ── SQLite connection (in-memory, mirrors sql/eda_queries.sql) ─────────────────
conn = sqlite3.connect(":memory:")
df.to_sql("packages", conn, index=False, if_exists="replace")


# ══════════════════════════════════════════════════════════════════════════════
# CSV 01 — Overall Summary
# ══════════════════════════════════════════════════════════════════════════════
summary = pd.read_sql("""
SELECT
    COUNT(*)                                         AS total_packages,
    SUM(delivery_failure)                            AS total_failures,
    ROUND(AVG(delivery_failure) * 100.0, 2)          AS failure_rate_pct,
    ROUND(AVG(cr_number_missing) * 100.0, 2)         AS cr_missing_pct,
    ROUND(AVG(double_scan)       * 100.0, 2)         AS double_scan_pct,
    ROUND(AVG(short_service_time) * 100.0, 2)        AS short_service_time_pct,
    COUNT(DISTINCT carrier)                          AS n_carriers,
    COUNT(DISTINCT shift)                            AS n_shifts,
    ROUND(AVG(route_distance_km), 2)                 AS avg_route_distance_km,
    MIN(route_distance_km)                           AS min_route_distance_km,
    MAX(route_distance_km)                           AS max_route_distance_km,
    MIN(packages_in_route)                           AS min_packages_in_route,
    MAX(packages_in_route)                           AS max_packages_in_route
FROM packages
""", conn)

# Append model metrics as columns
summary["model_name"]          = artifact["model_name"]
summary["model_auc_roc"]       = round(metrics["auc_roc"], 4)
summary["model_recall_at_t"]   = round(metrics["recall_optimized"], 4)
summary["model_threshold"]     = threshold
summary["packages_flagged"]    = int(preds.sum())
summary["dataset_source"]      = "Amazon LMRC 2021"
summary["dataset_location"]    = "Los Angeles, CA"
summary["dataset_period"]      = "July 2018"

out = OUT_DIR / "01_overall_summary.csv"
summary.to_csv(out, index=False)
print(f"  ✓  {out.name}")


# ══════════════════════════════════════════════════════════════════════════════
# CSV 02 — Failure Rate by Carrier
# ══════════════════════════════════════════════════════════════════════════════
carrier_df = pd.read_sql("""
SELECT
    carrier,
    COUNT(*)                                         AS total_packages,
    SUM(delivery_failure)                            AS failures,
    ROUND(AVG(delivery_failure) * 100.0, 2)          AS failure_rate_pct,
    ROUND(AVG(route_distance_km), 2)                 AS avg_route_distance_km,
    ROUND(MIN(route_distance_km), 2)                 AS min_route_distance_km,
    ROUND(MAX(route_distance_km), 2)                 AS max_route_distance_km,
    ROUND(AVG(packages_in_route), 1)                 AS avg_packages_in_route,
    COUNT(DISTINCT route_distance_km)                AS unique_routes
FROM packages
GROUP BY carrier
ORDER BY failure_rate_pct DESC
""", conn)

# Add vs-average delta
overall_rate = df["delivery_failure"].mean() * 100
carrier_df["vs_avg_pct_points"] = (carrier_df["failure_rate_pct"] - overall_rate).round(2)
carrier_df["risk_vs_avg"] = carrier_df["vs_avg_pct_points"].apply(
    lambda d: "Above average" if d > 0 else "Below average"
)

out = OUT_DIR / "02_failure_by_carrier.csv"
carrier_df.to_csv(out, index=False)
print(f"  ✓  {out.name}")


# ══════════════════════════════════════════════════════════════════════════════
# CSV 03 — Failure Rate by Shift
# ══════════════════════════════════════════════════════════════════════════════
shift_df = pd.read_sql("""
SELECT
    shift,
    COUNT(*)                                         AS total_packages,
    SUM(delivery_failure)                            AS failures,
    ROUND(AVG(delivery_failure) * 100.0, 2)          AS failure_rate_pct,
    ROUND(AVG(route_distance_km), 2)                 AS avg_route_distance_km,
    ROUND(AVG(packages_in_route), 1)                 AS avg_packages_in_route
FROM packages
GROUP BY shift
ORDER BY failure_rate_pct DESC
""", conn)

shift_df["vs_avg_pct_points"] = (shift_df["failure_rate_pct"] - overall_rate).round(2)
shift_df["shift_order"] = shift_df["shift"].map(
    {"morning": 1, "afternoon": 2, "night": 3}
).fillna(9).astype(int)

out = OUT_DIR / "03_failure_by_shift.csv"
shift_df.to_csv(out, index=False)
print(f"  ✓  {out.name}")


# ══════════════════════════════════════════════════════════════════════════════
# CSV 04 — Failure Rate by Package Type
# ══════════════════════════════════════════════════════════════════════════════
pkgtype_df = pd.read_sql("""
SELECT
    package_type,
    COUNT(*)                                         AS total_packages,
    SUM(delivery_failure)                            AS failures,
    ROUND(AVG(delivery_failure) * 100.0, 2)          AS failure_rate_pct,
    SUM(double_scan)                                 AS double_scan_count,
    SUM(short_service_time)                          AS short_service_time_count,
    SUM(cr_number_missing)                           AS cr_missing_count,
    ROUND(AVG(route_distance_km), 2)                 AS avg_route_distance_km
FROM packages
GROUP BY package_type
ORDER BY failure_rate_pct DESC
""", conn)

pkgtype_df["vs_avg_pct_points"] = (pkgtype_df["failure_rate_pct"] - overall_rate).round(2)

out = OUT_DIR / "04_failure_by_package_type.csv"
pkgtype_df.to_csv(out, index=False)
print(f"  ✓  {out.name}")


# ══════════════════════════════════════════════════════════════════════════════
# CSV 05 — Failure Rate by Route Distance Bucket
# ══════════════════════════════════════════════════════════════════════════════
distance_df = pd.read_sql("""
SELECT
    CASE
        WHEN route_distance_km < 40          THEN '1. Under 40 km'
        WHEN route_distance_km BETWEEN 40 AND 60 THEN '2. 40-60 km'
        ELSE                                      '3. Over 60 km'
    END                                           AS distance_bucket,
    CASE
        WHEN route_distance_km < 40          THEN 'Dense urban (< 40 km)'
        WHEN route_distance_km BETWEEN 40 AND 60 THEN 'Suburban mixed (40-60 km)'
        ELSE                                      'Long-haul (> 60 km)'
    END                                           AS distance_label,
    COUNT(*)                                      AS total_packages,
    SUM(delivery_failure)                         AS failures,
    ROUND(AVG(delivery_failure) * 100.0, 2)       AS failure_rate_pct,
    ROUND(AVG(route_distance_km), 2)              AS avg_route_distance_km,
    ROUND(MIN(route_distance_km), 2)              AS min_route_distance_km,
    ROUND(MAX(route_distance_km), 2)              AS max_route_distance_km,
    ROUND(AVG(packages_in_route), 1)              AS avg_packages_in_route
FROM packages
GROUP BY distance_bucket
ORDER BY distance_bucket
""", conn)

distance_df["vs_avg_pct_points"] = (distance_df["failure_rate_pct"] - overall_rate).round(2)
distance_df["urban_density_note"] = distance_df["distance_bucket"].map({
    "1. Under 40 km":  "Urban density paradox: dense LA areas have more access barriers",
    "2. 40-60 km":     "Suburban mix: moderate access complexity",
    "3. Over 60 km":   "Long-haul: single-family homes, direct door access",
})

out = OUT_DIR / "05_failure_by_distance.csv"
distance_df.to_csv(out, index=False)
print(f"  ✓  {out.name}")


# ══════════════════════════════════════════════════════════════════════════════
# CSV 06 — Operational Flags
# ══════════════════════════════════════════════════════════════════════════════
flags_df = pd.read_sql("""
SELECT 'double_scan'         AS flag, SUM(double_scan)         AS flagged_count,
       COUNT(*) AS total,   ROUND(AVG(double_scan)         * 100.0, 2) AS flag_rate_pct FROM packages
UNION ALL
SELECT 'short_service_time',  SUM(short_service_time),
       COUNT(*),              ROUND(AVG(short_service_time)  * 100.0, 2) FROM packages
UNION ALL
SELECT 'cr_number_missing',   SUM(cr_number_missing),
       COUNT(*),              ROUND(AVG(cr_number_missing)   * 100.0, 2) FROM packages
UNION ALL
SELECT 'delivery_failed',     SUM(delivery_failed),
       COUNT(*),              ROUND(AVG(delivery_failed)     * 100.0, 2) FROM packages
ORDER BY flagged_count DESC
""", conn)

# Add conditional failure rate when flag = 1
cond_rates = {}
for flag in ["double_scan", "short_service_time", "cr_number_missing", "delivery_failed"]:
    active = df[df[flag] == 1]
    if len(active) > 0:
        cond_rates[flag] = round(active["delivery_failure"].mean() * 100, 2)
    else:
        cond_rates[flag] = 0.0

flags_df["failure_rate_when_active_pct"] = flags_df["flag"].map(cond_rates)
flags_df["overall_failure_rate_pct"]     = round(overall_rate, 2)
flags_df["risk_multiplier"] = (
    flags_df["failure_rate_when_active_pct"] / overall_rate
).round(2)

flags_df["operational_action"] = flags_df["flag"].map({
    "delivery_failed":    "QA review — delivery attempt failed, investigate root cause",
    "short_service_time": "Verify locker/access availability before dispatch",
    "double_scan":        "Rescan / escalate to warehouse team",
    "cr_number_missing":  "Trigger customer contact before dispatch",
})

out = OUT_DIR / "06_operational_flags.csv"
flags_df.to_csv(out, index=False)
print(f"  ✓  {out.name}")


# ══════════════════════════════════════════════════════════════════════════════
# CSV 07 — Package-Level Predictions
# ══════════════════════════════════════════════════════════════════════════════
pred_df = df[[
    "package_id", "package_type", "shift", "carrier",
    "route_distance_km", "packages_in_route",
    "double_scan", "short_service_time", "cr_number_missing",
    "delivery_failure",
]].copy()

pred_df["failure_probability_pct"] = (probs * 100).round(2)
pred_df["predicted_failure"]       = preds
pred_df["risk_tier"]               = df["risk_tier"].astype(str)

pred_df["distance_bucket"] = pd.cut(
    pred_df["route_distance_km"],
    bins=[-1, 40, 60, 9_999],
    labels=["Under 40 km", "40-60 km", "Over 60 km"],
).astype(str)

# Outcome labels for Tableau filters
pred_df["actual_outcome"]    = pred_df["delivery_failure"].map(
    {0: "Delivered", 1: "Failed"}
)
pred_df["prediction_result"] = pred_df.apply(
    lambda r: "True Positive"  if r.predicted_failure == 1 and r.delivery_failure == 1 else
              "False Positive" if r.predicted_failure == 1 and r.delivery_failure == 0 else
              "True Negative"  if r.predicted_failure == 0 and r.delivery_failure == 0 else
              "False Negative",
    axis=1,
)

out = OUT_DIR / "07_package_predictions.csv"
pred_df.to_csv(out, index=False)
print(f"  ✓  {out.name}")


# ══════════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"  All 7 Tableau CSVs saved → {OUT_DIR}")
print(f"{'='*60}")

print("\n  CSV contents:")
for csv_file in sorted(OUT_DIR.glob("*.csv")):
    rows = pd.read_csv(csv_file)
    print(f"  {csv_file.name:<40}  {len(rows):>5} rows  x  {len(rows.columns)} cols")

print(f"\n  Model: {artifact['model_name']}")
print(f"  AUC-ROC      : {metrics['auc_roc']:.4f}")
print(f"  Recall@{threshold} : {metrics['recall_optimized']:.4f}  (80%)")
print(f"  Threshold    : {threshold}")
print(f"  Packages flagged as high-risk: {int(preds.sum())} / {len(df)}")
