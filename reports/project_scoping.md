# Project Scoping: Delivery Failure Prediction — Amazon LA

**Program:** Correlation One — DANA Week 12  
**Project Type:** Predictive Analytics / Machine Learning  
**Domain:** Last-Mile Logistics Operations  

---

## 1. Business Problem

Amazon LA's last-mile delivery network generates approximately **19% delivery failures** — packages that are not successfully delivered on the first attempt. These failures are currently diagnosed *after the fact*, making it impossible to intervene proactively.

**Core question:** Given what we know about a package at dispatch time, what is the probability it will fail to be delivered?

**Scope boundaries:**
- **In scope**: Pre-dispatch package scoring, carrier-level analysis, operational risk flags
- **Out of scope**: Real-time GPS tracking integration, customer demand forecasting, returns optimization

---

## 2. Business Impact

### Quantified Problem (Sample Dataset — 7,500 packages)
| Metric | Value |
|---|---|
| Total packages analyzed | 7,500 |
| Estimated failure rate | ~19.4% |
| Estimated failed deliveries | ~1,455 |
| Avg cost per failed delivery | $8–12 |
| **Total estimated cost in sample** | **$11,640–$17,460** |

### Key Impact Drivers

**Carrier D (Correos) + Routes > 50km** — this combination shows a ~21% incremental failure probability above baseline, representing a significant operational bottleneck.

**Damaged-on-Arrival** — packages arriving at the FC with damage have a ~55% additional failure probability, suggesting inspection-to-dispatch quality controls are critical.

**Night Shift + High Value** — courier fatigue and security concerns drive higher failure rates for premium packages on evening routes.

### If Model Deployed at Scale
A model catching 60% of true failures (recall ~0.46, validated) would allow pre-emptive intervention on hundreds of packages daily. Assuming $8 savings per prevented failure and 30% of flagged failures actually prevented:

> **Conservative annual savings estimate (LA network): $2–5M**

---

## 3. Data

### Datasets Used
| Dataset | Records | Purpose |
|---|---|---|
| `packages_train.csv` | 5,000 | Model training |
| `packages_validation.csv` | 1,500 | Model evaluation & tuning |
| `packages_test.csv` | 1,000 | Final holdout evaluation |

### Feature Categories
1. **Package characteristics**: type, days in FC, damaged on arrival
2. **Operational flags**: double scan, locker issue, missing CR number
3. **Route context**: distance, packages in route
4. **Carrier & shift**: who delivers it and when
5. **Environmental**: weather risk at delivery time

### Data Quality Notes
- No missing values (operationally controlled synthetic dataset)
- All categorical variables encoded via LabelEncoder for model ingestion
- Numerical features in natural scale (no normalization needed for RandomForest)
- Class imbalance: ~80/20 delivered/failed — addressed with `class_weight='balanced'`

---

## 4. Methods

### Model Selection: RandomForestClassifier
**Why RandomForest?**
- Handles mixed feature types (numerical + categorical encodings) natively
- Robust to outliers and non-linear feature interactions (e.g., carrier × distance)
- Provides native feature importance rankings — critical for operational explainability
- No feature scaling required — reduces preprocessing pipeline complexity
- Ensemble approach reduces overfitting compared to single decision trees

**Hyperparameters:**
```
n_estimators  = 200       # sufficient for stable importances
max_depth     = 8         # prevents overfitting on 5k samples
min_samples_split = 10
min_samples_leaf  = 5
class_weight  = 'balanced' # addresses 80/20 class imbalance
random_state  = 42
```

### Feature Engineering
All 4 categorical features are Label Encoded to numeric representations compatible with sklearn's RandomForest implementation. Resulting model features:

| Encoded Feature | Source |
|---|---|
| `package_type_enc` | package_type → integer |
| `shift_enc` | shift → integer |
| `carrier_enc` | carrier → integer |
| `weather_enc` | weather_risk → integer |
| `route_distance_km` | as-is |
| `packages_in_route` | as-is |
| `days_in_fc` | as-is |
| `double_scan` | binary, as-is |
| `locker_issue` | binary, as-is |
| `damaged_on_arrival` | binary, as-is |
| `cr_number_missing` | binary, as-is |

### Evaluation Metrics
- **AUC-ROC**: Primary metric — measures discrimination ability across all thresholds
- **Precision / Recall**: Operational trade-off analysis (false positives = wasted reviews; false negatives = undetected failures)
- **Confusion Matrix**: Absolute counts for business cost estimation
- **Average Precision (AP)**: Area under precision-recall curve for imbalanced class context

---

## 5. Deliverables

| # | Deliverable | Description | Format |
|---|---|---|---|
| 1 | Project Description | Business context and dataset documentation | Markdown report |
| 2 | Project Scoping | This document — problem framing and approach | Markdown report |
| 3 | Data Curation | Profiling, wrangling, encoding pipeline | Notebook + report |
| 4 | Exploratory Data Analysis | Univariate + bivariate analysis with business insights | Notebook + report |
| 5 | Trained Model Artifact | RandomForest pickle + evaluation plots | .pkl + PNG figures |
| 6 | Interactive Dashboard | Streamlit app with KPIs, charts, and prediction tool | Python app |
| 7 | Final Report | Comprehensive findings, recommendations, next steps | Markdown report |
| 8 | README | Setup guide and project overview | Markdown |

---

## 6. Milestones & Timeline

| Week | Milestone | Status |
|---|---|---|
| Week 10 | Data generation & project setup | Complete |
| Week 11 | EDA, feature engineering, model training | Complete |
| Week 12, Day 1–2 | Dashboard development | Complete |
| Week 12, Day 3 | Report writing & documentation | Complete |
| **Week 12 — Submission** | **Full portfolio submission** | **Ready** |

---

## 7. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Synthetic data not reflecting real operations | Medium | Medium | Correlations calibrated from published Amazon logistics benchmarks |
| Low recall on failure class (class imbalance) | High | Medium | `class_weight='balanced'` in model; threshold tuning in dashboard |
| Model interpretability concerns from ops team | Low | High | Feature importance chart and plain-language explanations in dashboard |
| Streamlit dashboard not running in target environment | Low | Low | requirements.txt pinned; tested locally |

---

*Scoping document prepared for Correlation One DANA Week 12 Final Portfolio Submission.*
