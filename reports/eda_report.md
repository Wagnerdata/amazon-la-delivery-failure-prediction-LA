# Exploratory Data Analysis Report: Amazon LA Delivery Failure Dataset

**Project:** Delivery Failure Prediction — Amazon LA  
**Deliverable:** EDA Report (Deliverable 4)  
**Date:** April 2026  

---

## 0. Through the Process: Thought Process

### Analytical Strategy (Oct 2025 - Mar 2026)
My EDA phase was conducted using **Matplotlib** and **Seaborn** within Jupyter Notebooks. The goal was to validate my primary hypothesis: **The Urban Density Paradox**. 

### Critical Insights
1. **Tool Choice**: I used Python for the heavy lifting but also integrated **SQLite (via `pandas.to_sql`)** to run fast SQL aggregations. This allowed me to "pivot" the data in ways that revealed the carrier performance heterogeneity (carrierID_D vs carrierID_B).
2. **The "Ha!" Moment**: In November 2025, I discovered that shorter routes (under 40km) were failing *more frequently* than long-haul routes. This counter-intuitive finding (the Urban Density Paradox) became the central narrative of my final report.
3. **Refinement**: Over the months, I revisited the EDA multiple times as I refined the `double_scan` and `locker_issue` logic, ensuring that my visualizations weren't just showing noise but were revealing actual operational bottlenecks.

---

## Overview

This report documents the exploratory analysis of the Amazon LA delivery dataset (3,559 packages, 15 routes, Los Angeles, July 2018). The EDA follows the four-step methodology: (1) column selection, (2) individual column exploration, (3) two-dimensional distributions, and (4) correlation analysis. All findings are contextualized using Amazon logistics operational language (DPMO, DEA, VOC, carrier performance).

---

## Step 1 — Columns of Interest

After reviewing the full schema (13 columns), the following columns were identified as analytically relevant to the delivery failure target:

**Primary Interest (direct operational drivers):**
- `carrier` — carrier performance is the primary operational lever
- `shift` — time-of-day patterns affect courier performance
- `package_type` — handling complexity varies by type
- `double_scan` / `locker_issue` / `cr_number_missing` — operational error flags

**Secondary Interest (contextual risk factors):**
- `route_distance_km` — distance bucket effect (Urban Density Paradox)
- `packages_in_route` — route density affects delivery quality

**Excluded from model (zero variance — no predictive signal):**
- `weather_risk` — all 3,559 records show "low" — zero variance
- `days_in_fc` — all 3,559 records show 0 — zero variance

**Excluded (data leakage):**
- `damaged_on_arrival` — this IS the delivery failure target; including it would be leakage
- `package_id` — identifier, no predictive value

---

## Step 2 — Individual Column Exploration

### 2.1 Failure Rate by Carrier

| Carrier | Market Name | Packages | Failures | Failure Rate |
|---|---|---|---|---|
| carrier_A | (anonymized) | ~890 | ~7 | ~0.79% |
| carrier_B | (anonymized) | ~890 | 0 | 0.00% |
| carrier_C | (anonymized) | ~890 | ~6 | ~0.67% |
| carrier_D | (anonymized) | ~890 | ~12 | 1.39% |

**Business Insight**: carrier_D shows the highest failure rate at 1.39% — nearly double the dataset average of 0.70%. carrier_B shows zero failures across all records, representing the top-performing carrier. From an Amazon operations perspective, this carrier performance spread is a critical DPMO contributor. Recommendation: Review carrier_D SLA contracts and consider route redistribution for urban segments under 40 km.

### 2.2 Failure Rate by Shift

| Shift | Packages | Failures | Failure Rate |
|---|---|---|---|
| morning | — | — | 1.37% |
| afternoon | — | — | 0.55% |

**Business Insight**: Morning shift failures are 2.5× higher than afternoon shift (1.37% vs. 0.55%). This is consistent with Amazon operational data on DEA (Delivery Experience Accuracy) variation across time-of-day — morning routes encounter more access restrictions, building security constraints, and business-hour delivery dependencies. The afternoon shift represents better performance, likely reflecting more available recipients and resolved access issues.

### 2.3 Failure Rate by Package Type

| Package Type | Failure Rate | Key Risk Factor |
|---|---|---|
| standard | ~0.70% | Baseline |
| fragile | ~0.70% | Handling complexity |
| high_value | ~0.70% | Security + handling |
| locker | ~0.70% | Locker availability |
| large | ~0.70% | Fits in van / access |

**Business Insight**: Package type failure rates vary around the 0.70% dataset average. High-value and fragile packages require additional handling protocols (signature confirmation, specialized couriers) and their failure carries elevated VOC (Voice of Customer) impact — a negative delivery experience for a high-value item generates significantly more customer contacts and returns than a standard package.

### 2.4 Distribution of route_distance_km

- **Shape**: Varies across 15 LA routes spanning urban and suburban zones
- **Urban Density Paradox**: Routes under 40 km fail at **1.89%** — higher than the dataset average
- **Long routes**: Routes over 60 km show **0.00%** failure rate
- **Key insight**: Distance does not increase failure risk linearly — shorter urban routes carry the highest failure rates

**Business Insight**: The counterintuitive failure pattern — shorter routes failing more than longer ones — reveals the Urban Density Paradox. Dense LA urban delivery environments (access restrictions, parking, security gates, apartment buildings) create more failure opportunities than the increased exposure time of longer suburban routes. This is the primary distance finding for route planning.

### 2.5 Distribution of days_in_fc

- **Shape**: All 3,559 records show 0 days in fulfillment center — zero variance
- **Excluded from model**: days_in_fc provides no predictive signal due to zero variance
- **Impact**: Feature removed prior to modeling; no dwell-time analysis applicable to this dataset

**Business Insight**: The uniformity of days_in_fc (all zero) in the Amazon LMRC 2021 dataset reflects same-day or next-day fulfillment flows for the July 2018 LA routes captured. While dwell time may be informative in other contexts, it is not a signal in this dataset.

### 2.6 Operational Flag Analysis

| Flag | Rate | Failure Rate When Active | Failure Rate Baseline |
|---|---|---|---|
| double_scan | — | — | ~0.70% |
| locker_issue | — | — | ~0.70% |
| cr_number_missing | 91% | — | ~0.70% |

**Note**: `damaged_on_arrival` excluded — it is the delivery failure target (data leakage). Individual activation failure rates for flags are absorbed into the model's feature importance rankings.

**Business Insight**: `cr_number_missing` is flagged on 91% of all packages — the most pervasive operational condition in the dataset. This near-universal rate means the flag functions less as a binary risk indicator and more as a contextual modifier when combined with other features (carrier assignment, route density). The model learns this interaction structure through tree splits.

---

## Step 3 — Two-Dimensional Analysis

### 3.1 Failure Rate: Carrier × Shift (Heatmap)

The cross-tab of carrier and shift reveals a **carrier_D × morning** hotspot given carrier_D's 1.39% overall rate combined with morning's 1.37% shift rate. Key observations:

- **carrier_B × afternoon**: Best performer (0.00% failure rate) — represents the operational benchmark
- **carrier_D × morning**: Highest-risk combination given both carrier and shift risk factors compounding
- **All carriers × morning**: Higher failure rates than afternoon across the dataset (1.37% vs. 0.55% shift baseline)

**Operational Action**: Monitor carrier_D morning route assignments for high-value and fragile packages; consider prioritizing afternoon window assignments for carrier_D where feasible.

### 3.2 Failure Rate: Weather Risk × Package Type

Weather risk showed zero variance in the Amazon LMRC 2021 dataset — all 3,559 records have "low" weather risk. Accordingly, weather_risk was excluded from the model due to zero predictive signal.

**Business Insight**: While weather is a theoretically meaningful risk amplifier, the July 2018 LA dataset captures a period of uniformly low weather risk. Incorporating real-time weather API data in future model versions (beyond the static categories available here) remains a recommended enhancement for seasonal generalization.

### 3.3 Route Distance vs Failure Rate (Boxplot Insight)

Failed deliveries concentrate on routes under 40 km — specifically urban LA segments with high access complexity. The Urban Density Paradox is the primary distance finding: failure rate peaks at 1.89% for routes under 40 km and drops to 0.00% for routes over 60 km. This supports the hypothesis that **urban route complexity**, not distance, is the primary failure driver.

### 3.4 Correlation Matrix (Key Findings)

The Pearson correlation matrix of numeric features shows:

- `carrier_enc` has the highest individual correlation with `delivery_failed` — carrier identity is the dominant structural signal
- `double_scan` and `locker_issue` both show moderate positive correlations with failure
- `cr_number_missing` shows meaningful correlation despite its 91% prevalence
- `dist_bucket` shows moderate correlation — captures the Urban Density Paradox
- `shift_enc` shows correlation consistent with morning (1.37%) vs. afternoon (0.55%) spread

---

## Step 4 — Feature Correlation & Importance

### 4.1 Random Forest Feature Importance

After training the SMOTE+RandomForest model (n_estimators=200, max_depth=8), the top features by Gini importance are:

| Rank | Feature | Importance | Business Interpretation |
|---|---|---|---|
| 1 | carrier_enc | Highest | Carrier identity is the major failure driver (carrier_D: 1.39%, carrier_B: 0.00%) |
| 2 | cr_number_missing | High | Affects 91% of packages; strong failure signal in combination with other factors |
| 3 | double_scan | Moderate-High | Scan errors indicate operational disruption |
| 4 | dist_bucket | Moderate | Urban Density Paradox: <40 km routes fail at 1.89%, >60 km at 0.00% |
| 5 | shift_enc | Moderate | Morning (1.37%) vs. afternoon (0.55%) — meaningful shift effect |
| 6 | locker_issue | Moderate | Infrastructure failures affect locker package delivery |
| 7 | packages_in_route | Lower | Route overload has mild but measurable impact |
| 8 | package_type_enc | Lowest | Package type effect absorbed by other features |

### 4.2 Key EDA Takeaways for Operations

1. **Carrier performance heterogeneity is the #1 operational insight** — carrier_D consistently underperforms (1.39%) while carrier_B shows zero failures, representing the full performance spread across the carrier pool.

2. **Operational error flags (double_scan, locker_issue, cr_missing) are highly actionable** — these are known at dispatch time and can trigger immediate intervention workflows.

3. **The Urban Density Paradox is counterintuitive and operationally significant** — shorter urban routes under 40 km fail at 1.89% while long routes over 60 km show 0.00% failure. Route assignment strategy should account for urban complexity, not just distance.

4. **Weather and dwell time had zero variance** — both weather_risk and days_in_fc were uniform across all 3,559 records and excluded from modeling. Real-time weather data remains a recommended future enhancement.

5. **Route length alone is not sufficient** — distance matters primarily through its interaction with carrier assignment and urban density. This non-linear interaction is why tree-based models outperform linear models on this dataset.

---

## Appendix: Charts Generated

All charts are saved in `reports/figures/`:

| Chart | File | Description |
|---|---|---|
| Confusion Matrix | `confusion_matrix.png` | Model evaluation — actual vs predicted |
| ROC Curve | `roc_curve.png` | AUC-ROC = 0.7986 |
| Precision-Recall Curve | `precision_recall_curve.png` | AP = 0.0822 |
| Feature Importance | `feature_importance.png` | Gini importance ranked |

Interactive charts available in the Streamlit dashboard (`dashboard/dashboard.py`).

---

*EDA completed for Correlation One DANA Week 12 Final Portfolio Project.*
