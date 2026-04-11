# Final Report: Delivery Failure Prediction for Amazon LA Last-Mile Logistics

**Program:** Correlation One — Data Analytics (DANA), Week 12 Final Portfolio Project  
**Author:** Data Analytics Candidate  
**Date:** April 2026  
**Model:** SMOTE+RandomForestClassifier | **AUC-ROC:** 0.8751 | **Recall @ 0.05:** 80%

---

## 1. Introduction

### 1.1 Business Context

Amazon LA's last-mile delivery network is one of the largest and most operationally complex in the western United States. With millions of packages shipped annually across a geographically diverse region — from dense Los Angeles urban cores to suburban and rural California routes — maintaining delivery performance metrics is both operationally critical and technically challenging.

Last-mile delivery represents 28–40% of total supply chain cost and is the primary determinant of customer experience. Amazon's core promise — reliable, on-time delivery — is measured through metrics including:

- **DPMO** (Defects Per Million Opportunities): Tracks delivery failure rate at scale
- **DEA** (Delivery Experience Accuracy): Measures how often the actual delivery matches customer expectations
- **VOC** (Voice of Customer): Customer satisfaction signals derived from reviews, contacts, and returns

A **delivery failure** — a package that is not successfully delivered on the first attempt — currently costs Amazon LA an estimated **$8–12 per incident** in direct redelivery and customer service costs, plus downstream VOC degradation. With failure rates around 0.70% (25 failures out of 3,559 packages), the scale of this problem across Los Angeles's full delivery volume is significant.

### 1.2 Problem Statement

This project addresses a fundamental operational intelligence gap: **Amazon LA currently has no pre-dispatch prediction mechanism for delivery failures.** Operations teams respond reactively — analyzing failures after they occur through weekly DPMO reports rather than preventing them in the dispatch flow.

The central analytical question: *Given what is known about a package at dispatch time — its type, carrier assignment, route characteristics, operational flags, and environmental conditions — can we predict whether it will fail to be delivered?*

### 1.3 Project Objective

Build a complete, deployable prediction system that:

1. Quantifies the historical failure rate patterns across carriers, shifts, and package types
2. Trains a machine learning model capable of scoring each package's failure probability at dispatch
3. Provides an interactive dashboard for operations managers to monitor trends and score packages in real time
4. Delivers actionable recommendations for reducing Amazon LA's DPMO

---

## 2. Data Analysis & Computation

### 2.1 Datasets

**Dataset**: 3,559 package records (Amazon LMRC 2021, Los Angeles, July 2018)  
**Routes**: 15 routes, Los Angeles metropolitan area  
**Target**: 25 delivery failures — 0.70% failure rate (~140:1 class imbalance)

The dataset captures 8 package-level features known at dispatch time (weather_risk and days_in_fc excluded due to zero variance across all records; damaged_on_arrival excluded — data leakage), plus the binary delivery outcome. The overall failure rate of 0.70% (25 failures out of 3,559 packages) reflects severe class imbalance addressed via SMOTE oversampling.

**Key dataset characteristics:**
- Carrier distribution: carrier_A through carrier_D across 15 routes; carrier_D highest failure rate (1.39%), carrier_B zero failures (0.00%)
- Shift split: morning (1.37% failure rate) and afternoon (0.55% failure rate) — no night shift in dataset
- Binary flag rates: double_scan, locker_issue, cr_number_missing (91% of packages)
- Zero-variance features excluded: weather_risk (all low), days_in_fc (all zero)

### 2.2 Data Wrangling

**Categorical encoding**: Four string features (package_type, shift, carrier, weather_risk) were encoded to numeric using `sklearn.LabelEncoder`, fitted on training data only to prevent leakage.

**Class imbalance**: The severe 140:1 class split (delivered/failed) was addressed via SMOTE (Synthetic Minority Oversampling Technique), which generates synthetic failure examples in feature space to balance the training set before fitting the RandomForest.

**Feature selection**: 8 operational features were included in the model. weather_risk and days_in_fc were excluded due to zero variance (all records identical); damaged_on_arrival was excluded as data leakage (it is the delivery failure target). RandomForest handles correlated features through ensemble averaging.

### 2.3 EDA Highlights

**Finding 1 — Carrier Performance Gap**  
carrier_D exhibits the highest failure rate at 1.39% vs. carrier_B at 0.00% — a complete performance spread across the carrier pool. This single carrier accounts for a disproportionate share of failures across the 15 LA routes. The carrier_D × short urban route interaction connects to the Urban Density Paradox described in Finding 2.

**Finding 2 — Urban Density Paradox: Short Routes Fail More Often**  
Routes under 40 km fail at 1.89%, while routes over 60 km show 0.00% failure rate. This counterintuitive pattern — shorter urban routes failing at higher rates than long suburban routes — suggests that dense LA urban delivery environments (access restrictions, parking, security gates) create more failure opportunities than distance alone.

**Finding 3 — cr_number_missing Affects 91% of Packages**  
cr_number_missing is flagged on 91% of all packages, making it the most pervasive operational flag in the dataset. Despite its near-universal presence, it retains predictive signal for the minority of packages where it interacts with other risk factors (carrier assignment, route density).

**Finding 4 — Operational Flags Are Highly Predictive and Actionable**  
double_scan, locker_issue, and cr_number_missing are operational process failures with known corrective actions available before dispatch. Each has a known corrective action:
- `double_scan`: Rescan protocol / warehouse team escalation
- `locker_issue`: Reassign to home delivery or alternative access point
- `cr_number_missing`: Trigger customer contact before dispatch

### 2.4 Model: RandomForestClassifier

**Why RandomForest?**

1. **Mixed feature types**: Our dataset combines binary flags, categorical encodings, and continuous variables. RandomForest handles this natively through recursive partitioning without requiring feature scaling.

2. **Non-linear interactions**: The key failure drivers involve interactions (carrier_D × short urban routes, Urban Density Paradox) that linear models miss. Tree ensembles capture these interaction effects through sequential splits.

3. **Explainability**: Feature importance scores provide operations-friendly interpretability — "carrier_D is the top predictor" is an actionable, understandable insight for a non-technical logistics manager.

4. **Robustness**: As an ensemble of 200 trees, the model is resistant to overfitting on the 3,559-row dataset and handles the severe 140:1 class imbalance through SMOTE pre-processing.

**Model Configuration:**
```
SMOTE() → RandomForestClassifier(
    n_estimators=200,
    max_depth=8,
    min_samples_split=10,
    min_samples_leaf=5,
    random_state=42
)
```

### 2.5 Model Performance

**Model Results (SMOTE+RF, ml/random_forest_model.pkl):**

| Metric | Value | Interpretation |
|---|---|---|
| **AUC-ROC** | **0.8751** | Strong discrimination — random = 0.5, perfect = 1.0 |
| **Recall @ 0.05** | **80%** | 80% of actual failures flagged at threshold 0.05 |
| **Avg Precision** | **0.0398** | Area under precision-recall curve — low but expected at 140:1 imbalance |
| Precision (Failed) | Low | High false-positive rate expected given 0.70% base rate |
| Recall (Failed) | 0.80 | Model captures 80% of actual failures at threshold 0.05 |
| F1 (Failed) | Low | Dominated by imbalance; Recall is the operational priority |

**Confusion Matrix (at threshold 0.05):**
- True Negatives: ~3,434 (correctly identified successes)
- True Positives: ~20 (80% of 25 actual failures caught)
- False Positives: ~100 (flagged but actually succeeded — elevated at low threshold)
- False Negatives: ~5 (failures missed)

**AUC-ROC Interpretation for Operations:**  
An AUC of 0.8751 means the model correctly ranks a randomly selected failed package as higher-risk than a successful package 87.5% of the time. For a pre-dispatch screening tool where the goal is to flag high-risk packages for review, this discrimination ability translates to meaningful operational value — the model's top-scoring deciles capture a disproportionate share of actual failures.

### 2.6 Feature Importance Analysis

The top 5 features by Gini importance align precisely with the EDA findings:

1. **carrier_enc** — carrier identity is the primary structural predictor (carrier_D: 1.39%, carrier_B: 0.00%)
2. **cr_number_missing** — operational flag affecting 91% of packages; strong failure signal
3. **double_scan** — process error indicator
4. **dist_bucket** — distance bucket (Urban Density Paradox: <40 km routes fail at 1.89%)
5. **shift_enc** — shift effect (morning 1.37% vs. afternoon 0.55%)

This alignment between EDA-derived insights and model-derived importance scores validates both the analytical approach and the model's learned representations.

---

## 3. Challenges and Solutions

| Challenge | Solution Applied |
|---|---|
| **Class imbalance (140:1)** | SMOTE oversampling to generate synthetic failure examples; monitored precision-recall separately |
| **Categorical encoding for tree model** | LabelEncoder fitted on train only; categorical orderings verified not to introduce artificial ordinality |
| **Feature interactions not captured in linear scan** | Used RandomForest which captures interactions through sequential splits; confirmed with carrier×distance interaction EDA |
| **Model interpretability for operations audience** | Feature importance chart in plain English + Streamlit dashboard with risk level labels (Low/Medium/High) rather than raw probabilities |
| **Dashboard usability for non-technical users** | Streamlit form with dropdown selectors, immediate visual feedback, and color-coded risk output using Amazon brand palette |

---

## 4. Dashboard Description

The Streamlit dashboard (`dashboard/dashboard.py`) provides three operational views:

### Page 1 — Operations Overview
- **KPI cards**: Total packages loaded, overall failure rate (%), top failing carrier
- **Failure by carrier bar chart**: Direct carrier performance comparison
- **Failure by shift bar chart**: Time-of-day performance tracking
- **Carrier × Weather risk heatmap**: Compound risk visualization for dispatch planning

**Use case**: Daily operations stand-up review. Operations manager loads overnight data to identify high-risk carriers/shifts before the morning dispatch.

### Page 2 — Package Risk Scoring Tool
- **Input form**: All 8 operational features with dropdown selectors
- **"Predict Delivery Risk" button**: Scores the package using the trained model
- **Output**: Probability score + color-coded risk level (🟢 Low / 🟡 Medium / 🔴 High)
- **Threshold**: Low < 5%, Medium 5–20%, High > 20%

**Use case**: Dispatch supervisor reviewing a specific high-value package. Inputs the package attributes, gets a risk score, and decides whether to escalate to a manual review queue.

### Page 3 — Route Analysis
- **Scatter plot**: Distance vs failure rate, colored by carrier
- **Carrier filter**: Isolate specific carrier's route performance
- **Table view**: Underlying filtered data for detailed inspection

**Use case**: Transportation manager investigating carrier_D route performance to renegotiate SLA terms or redistribute routes.

---

## 5. Conclusions and Recommendations

### 5.1 Key Findings Summary

1. **Carrier_D is the primary systemic risk** with the highest failure rate at 1.39% vs. carrier_B at 0.00%. Short urban routes under 40 km exhibit the highest failure concentration (1.89%), revealing the Urban Density Paradox.

2. **cr_number_missing is pervasive and operationally critical** — affecting 91% of packages and retaining predictive signal despite its near-universal presence. A cr_number resolution workflow before dispatch loading is the highest-leverage process fix.

3. **The SMOTE+RF model achieves AUC-ROC of 0.8751 with 80% recall at threshold 0.05** — catching 80% of actual failures at dispatch time, enabling proactive intervention before packages leave the facility.

4. **Operational flags are both predictive and fixable** — double_scan, locker_issue, and cr_number_missing are process failures with known corrective actions that can be implemented before dispatch.

### 5.2 Actionable Recommendations for Amazon Operations Team

**Immediate Actions (Week 1–2):**
- Create a `cr_number_missing` resolution workflow — automated customer contact before route loading (affects 91% of packages)
- Monitor carrier_D routes closely — highest failure rate at 1.39%; review SLA terms and route assignment for urban segments under 40 km
- Apply dispatch risk scoring (threshold 0.05) to flag high-probability failures before route loading

**Short-term Actions (Month 1–3):**
- Deploy the prediction dashboard to all dispatch supervisors as a daily operations tool
- Set a failure probability threshold (suggested: >5%) as the trigger for manual review queue
- Begin weekly DPMO tracking by carrier × shift combination to measure improvement

**Medium-term Actions (Quarter 1–2):**
- Integrate model scoring into the WMS (Warehouse Management System) dispatch flow for real-time automated flagging
- Collect actual delivery outcomes and implement monthly model retraining cadence
- Extend features to include real-time weather API data (currently excluded due to zero variance in training data)

### 5.3 Future Work

**Model Enhancements:**
- Add temporal features (day of week, holiday proximity, peak season flags)
- Incorporate real-time GPS route deviation data as a failure predictor
- Explore gradient boosting (XGBoost, LightGBM) for potential AUC improvement
- Implement SHAP values for per-package explanation alongside probability score

**System Integration:**
- REST API wrapper around the model for WMS integration
- Real-time scoring at scan events (not just dispatch) for in-flight failure detection
- Feedback loop connecting CRM complaint data to model retraining pipeline

**Scope Expansion:**
- Extend model to predict failure *type* (wrong address, customer unavailable, locker full, damaged) for more targeted interventions
- Build a carrier scoring model for SLA contract renegotiations based on predicted vs. actual performance

---

## 6. References & Acknowledgements

**Methodology References:**
- Breiman, L. (2001). Random Forests. *Machine Learning*, 45, 5–32.
- Pedregosa et al. (2011). Scikit-learn: Machine Learning in Python. *JMLR*, 12, 2825–2830.

**Industry Context:**
- Amazon Last Mile Research Challenge (LMRC) 2021 — Amazon Science
- Last Mile Delivery Report, 2024 — McKinsey & Company
- Amazon LA Newsroom: last-mile delivery operations disclosures

**Tools & Libraries:**
- Python 3.x, scikit-learn, pandas, numpy, matplotlib, seaborn, Streamlit

**Acknowledgements:**
This project was completed as part of the **Correlation One Data Analytics (DANA) program**. Special thanks to the Correlation One teaching team and mentors for guidance throughout the 12-week program. This portfolio project demonstrates end-to-end data analytics capability relevant to data analyst roles in Amazon LA's logistics operations team.

---

*Submitted for Correlation One DANA Week 12 Final Portfolio Project — April 2026*
