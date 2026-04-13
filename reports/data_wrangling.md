# Data Wrangling Documentation
## Amazon Last Mile Delivery Failure Prediction
**Program:** Correlation One — DANA, Week 12 Final Project  
**Dataset:** Amazon Last Mile Routing Research Challenge (ALMRRC 2021)  
**Date:** April 2026

---

## 1. Source Dataset

| Attribute | Value |
|-----------|-------|
| File | `data/packages_validation.csv` |
| Source | Amazon Last Mile Routing Research Challenge (ALMRRC 2021) — public dataset |
| Script | `data/build_dataset.py` — streams route + package data from S3 |
| Geography | Los Angeles, CA |
| Period | July 2018 |
| Rows | 3,559 packages |
| Routes | 15 delivery routes |
| Columns (raw) | 12 |
| Missing values | 0 |
| Duplicate rows | 0 |

---

## 2. Raw Schema

| Column | Type | Description |
|--------|------|-------------|
| `package_id` | string | Unique package identifier — excluded (no predictive value) |
| `package_type` | categorical | `standard` / `high_value` |
| `shift` | categorical | `morning` / `afternoon` |
| `carrier` | categorical | `carrier_A` / `carrier_B` / `carrier_C` / `carrier_D` |
| `route_distance_km` | float | Total route distance: 25.9 – 80.6 km |
| `packages_in_route` | int | Route load: 196 – 276 packages |
| `weather_risk` | categorical | Constant = `"low"` — **zero variance** |
| `days_in_fc` | int | Constant = `0` — **zero variance** |
| `double_scan` | binary 0/1 | Package scanned at more than one stop (0.11% rate) |
| `locker_issue` | binary 0/1 | Failed delivery with short service time (0.17% rate) |
| `damaged_on_arrival` | binary 0/1 | `scan_status == "DELIVERY_ATTEMPTED"` — **is the target** |
| `cr_number_missing` | binary 0/1 | No time window / customer reference (91.06% rate) |

---

## 3. Target Variable Derivation

The raw CSV has no explicit `delivery_failure` column. The delivery outcome is stored in `damaged_on_arrival`, which is derived in `data/build_dataset.py` from the ALMRRC source field:

```
scan_status == "DELIVERY_ATTEMPTED"  →  damaged_on_arrival = 1  (failure)
scan_status == "DELIVERED"           →  damaged_on_arrival = 0  (success)
```

**Wrangling step applied in both notebooks and modeling scripts:**

```python
df['delivery_failure'] = df['damaged_on_arrival']
```

This promotes the signal to its canonical name. `damaged_on_arrival` is then **excluded from the feature set** in all modeling steps to prevent target leakage.

**Target distribution:**

| Class | Count | Rate |
|-------|-------|------|
| Delivered (0) | 3,534 | 99.30% |
| Failed (1) | 25 | 0.70% |
| **Class ratio** | | **~140:1** |

---

## 4. Zero-Variance Columns — Dropped

Two columns are constant across all 3,559 rows and provide no predictive signal:

| Column | Unique values | Action |
|--------|--------------|--------|
| `weather_risk` | `["low"]` | **Dropped** — zero variance |
| `days_in_fc` | `[0]` | **Dropped** — zero variance |

These are artifacts of the LA July 2018 extract: all routes were summer routes (weather = low) and all packages were dispatched same-day (days_in_fc = 0). The values would differ in a broader temporal extract.

---

## 5. Categorical Encoding

Three categorical columns were encoded to integer using `sklearn.LabelEncoder`, fitted on the validation set:

| Column | Encoded name | Classes | Encoded values |
|--------|-------------|---------|----------------|
| `carrier` | `carrier_enc` | carrier_A, carrier_B, carrier_C, carrier_D | 0, 1, 2, 3 |
| `shift` | `shift_enc` | afternoon, morning | 0, 1 |
| `package_type` | `package_type_enc` | high_value, standard | 0, 1 |

The encoders are saved in `ml/random_forest_model.pkl` under the `encoders` key so that new packages can be scored at inference time using the same mapping.

---

## 6. Route Distance Bucketing

`route_distance_km` (continuous) was binned into three operational buckets for both the model feature and the EDA GROUP BY queries:

| Bucket | Range | Label | Packages | Failure rate |
|--------|-------|-------|----------|-------------|
| 0 | < 40 km | Dense urban | 1,006 | **1.89%** |
| 1 | 40–60 km | Suburban mixed | 2,141 | 0.28% |
| 2 | > 60 km | Long-haul | 412 | **0.00%** |

```python
df['dist_bucket'] = pd.cut(
    df['route_distance_km'],
    bins=[-1, 40, 60, 9999],
    labels=[0, 1, 2]
).astype(int)
```

This bucketing was chosen because it aligns with the Urban Density Paradox finding: the three buckets capture meaningfully different access environments in Los Angeles, not just statistical terciles.

---

## 7. Final Feature Set

After dropping zero-variance, identifier, and leakage columns, the model uses 8 features:

| Feature | Type | Source | Rationale |
|---------|------|---------|-----------|
| `carrier_enc` | int | Encoded `carrier` | Highest structural predictor (1.39% vs 0.00% across carriers) |
| `shift_enc` | int | Encoded `shift` | Morning 1.37% vs afternoon 0.55% |
| `package_type_enc` | int | Encoded `package_type` | Standard vs high_value handling requirements |
| `dist_bucket` | int | Bucketed `route_distance_km` | Captures urban density paradox (0/1/2) |
| `packages_in_route` | int | Raw column | Route density (196–276) |
| `double_scan` | binary | Raw column | Scan anomaly flag (0.11% rate) |
| `locker_issue` | binary | Raw column | Locker access failure flag (0.17% rate) |
| `cr_number_missing` | binary | Raw column | Missing customer reference (91% rate) |

**Excluded columns and reasons:**

| Column | Reason excluded |
|--------|----------------|
| `package_id` | Identifier — no predictive value |
| `weather_risk` | Zero variance (constant = "low") |
| `days_in_fc` | Zero variance (constant = 0) |
| `damaged_on_arrival` | **Target proxy** — identical to `delivery_failure`, data leakage |
| `route_distance_km` | Replaced by `dist_bucket` (non-linear effect better captured by bins) |

---

## 8. Class Imbalance Handling

The 140:1 class ratio was addressed with two strategies compared in `notebooks/05_final_analysis.ipynb`:

| Strategy | Mechanism | Result |
|----------|-----------|--------|
| `class_weight='balanced'` | Upweights each failure sample by ~140× in the loss function | AUC-ROC ~0.87 |
| **SMOTE** (selected) | Generates synthetic minority samples in feature space before training | **AUC-ROC 0.8751, Recall 80%** |

SMOTE was applied **only to the training split** — never to the test set. `k_neighbors` was set to `min(5, n_failures_in_train - 1)` to handle the very small minority class.

---

## 9. Threshold Optimization

The default classification threshold (0.5) is calibrated for balanced classes. With a 140:1 imbalance and a business objective of maximizing recall (missed failures cost ~$17 each in redelivery + VOC degradation), the threshold was lowered to **0.05**.

| Threshold | Recall | Precision | Notes |
|-----------|--------|-----------|-------|
| 0.50 (default) | ~0.20 | ~0.50 | Too conservative — misses most failures |
| **0.05 (selected)** | **0.80** | **0.026** | Catches 80% of failures; 890 packages flagged for review |
| 0.01 | ~1.00 | ~0.003 | Near-perfect recall but flags 99%+ of all packages |

At threshold 0.05: **21 of 25 actual failures are caught** (4 missed). 869 false positives represent ~25% of the route requiring a quick pre-dispatch review — operationally feasible.

---

## 10. SQLite EDA Queries — Consistency Verification

All GROUP BY statistics used in the EDA notebook (`notebooks/04_eda_validation.ipynb`) were verified against `sql/eda_queries.sql` run via `sql/run_eda.py`. The Tableau CSVs were generated using the same SQLite queries so the numbers are identical across all documents.

**Verified figures (sql/eda_results.txt ↔ Tableau CSVs ↔ EDA notebook):**

| Metric | SQL result | Model finding |
|--------|-----------|---------------|
| Total packages | 3,559 | ✓ |
| Total failures | 25 (0.70%) | ✓ |
| carrier_D failure rate | 1.39% | ✓ Top carrier feature |
| carrier_B failure rate | 0.00% | ✓ |
| Morning shift failure rate | 1.37% | ✓ shift_enc in top features |
| Afternoon shift failure rate | 0.55% | ✓ |
| Routes < 40 km failure rate | 1.89% | ✓ dist_bucket=0 dominant |
| Routes > 60 km failure rate | 0.00% | ✓ dist_bucket=2 = zero risk |
| cr_number_missing rate | 91.06% | ✓ Included in features |

---

## 11. Inconsistencies Found During Audit

The following inconsistencies exist between project documents and should be corrected before submission:

| File | Issue | Correct value |
|------|-------|--------------|
| `reports/final_report.md` line 6 | States `AUC-ROC: 0.7110` | Correct AUC is **0.8751** (SMOTE+RF in `ml/random_forest_model.pkl`) |
| `reports/final_report.md` line 50 | States "~0.70% failure rate" | Correct rate is **0.70%** (25/3,559) |
| `reports/final_report.md` line 55 | States "damaged_on_arrival (4%), double_scan (8%)" | Correct rates: **0.70%, 0.11%** |
| `reports/eda_report.md` | Entire document describes the **synthetic** `packages_train.csv` dataset (5,000 rows, 3 shifts, ~19% failure rate) | Should describe `packages_validation.csv` (3,559 rows, 2 shifts, 0.70% failure rate) |
| `artifacts/delivery_model.pkl` | Stale model trained on synthetic data with data leakage (`damaged_on_arrival` as feature) — AUC 0.5927 | Use `ml/random_forest_model.pkl` (AUC 0.8751) |
| `train_model.py` line 57 | Includes `damaged_on_arrival` in `BINARY_FEATURES` | Must be excluded — it IS the target in validation data |

---

## 12. Tableau CSV Inventory

Generated by `scripts/generate_tableau_csvs.py` → `reports/tableau/`

| File | Rows | Columns | Content |
|------|------|---------|---------|
| `01_overall_summary.csv` | 1 | 21 | KPIs: total packages, failure rate, model metrics |
| `02_failure_by_carrier.csv` | 4 | 11 | Failure rate per carrier + vs-average delta |
| `03_failure_by_shift.csv` | 2 | 8 | Failure rate per shift + ordering column |
| `04_failure_by_package_type.csv` | 2 | 9 | Failure rate per package type + flag counts |
| `05_failure_by_distance.csv` | 3 | 11 | Failure rate per distance bucket + context notes |
| `06_operational_flags.csv` | 4 | 8 | Flag rates, conditional failure rates, risk multiplier, recommended action |
| `07_package_predictions.csv` | 3,559 | 16 | Every package with predicted probability, risk tier, TP/FP/FN label |

**`07_package_predictions.csv` confusion matrix summary:**

| Result | Count |
|--------|-------|
| True Positives (failures caught) | 21 |
| False Negatives (failures missed) | 4 |
| False Positives (false alarms) | 869 |
| True Negatives (correct clears) | 2,665 |

---

*Generated: April 2026 — Correlation One DANA Week 12 Final Portfolio Project*
