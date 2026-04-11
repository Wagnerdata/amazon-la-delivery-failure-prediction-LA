# Last-Mile Delivery Failure Prediction
### AI-powered pre-departure risk scoring for Amazon logistics operations

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3%2B-orange?logo=scikit-learn&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-2.0%2B-150458?logo=pandas&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Project History

This system was originally developed in October 2025 as a personal research project to explore whether last-mile delivery failures could be predicted before a package leaves the fulfillment center. The initial version used synthetic delivery data to build and validate the full technical architecture.

In April 2026, the system was adapted for the **Correlation One Data Analytics program (Week 12)** using real operational data from the Amazon Last Mile Routing Research Challenge (Los Angeles, 2018).

---

## The Business Problem

Every failed last-mile delivery costs approximately $17 — the carrier pays once for the failed attempt and again for the re-attempt, customer contact, and rescheduling. Across a network moving millions of packages daily, even a 1% failure rate compounds into a significant P&L impact.

Most attention in delivery logistics focuses on what happens on the road. This project focuses on what is already knowable before the truck leaves — carrier identity, shift time, route characteristics, and package-level flags that a dispatcher could act on in a morning briefing.

---

## Dataset

**Source:** Amazon Last Mile Routing Research Challenge (LMRC 2021)  
**Location:** Los Angeles, California — 15 routes, July 2018  
**Packages:** 3,559 real packages  
**Target:** `delivery_failure` (0.7% positive rate — 25 failures)  
**Access:** Public S3 bucket, no credentials required  

Key finding: routes under 40 km fail at 1.89% vs 0% for routes over 60 km — counterintuitive because short routes in LA cover dense urban areas with locked lobbies, locker access issues, and higher delivery complexity per stop.

---

## System Architecture

The system has three layers:

**1. Prediction Model** — Random Forest classifier trained on carrier, shift, route distance, package type, and operational flags. Optimized for recall (catching failures matters more than avoiding false positives). AUC-ROC: 0.8751.

**2. CrewAI Agent Layer** — Per-package executive reports generated for each high-risk package. The agent translates model feature importances into plain-language explanations a dispatcher can act on: "This package is flagged because it is on a morning route under 40 km assigned to carrier_D."

**3. REST API** — Serves predictions and agent reports to downstream systems or dashboard consumers.

---

## Key Results

| Metric | Value |
|---|---|
| Packages analyzed | 3,559 |
| Overall failure rate | 0.70% |
| AUC-ROC | 0.8751 |
| Recall at optimized threshold | 80% |
| Highest-risk carrier | carrier_D (1.39%) |
| Highest-risk shift | Morning (1.37%) |
| Highest-risk route bucket | < 40 km (1.89%) |

---

## Project Structure

```
delivery-failure-prediction/
├── deliverables/          ← Correlation One academic documents
│   ├── 01_project_description.docx
│   ├── 02_project_scoping.docx
│   ├── 03_data_curation.docx
│   ├── 04_eda.docx
│   ├── 05_datafolio.pptx
│   └── 07_final_report.docx
├── notebooks/
│   ├── 04_eda_validation.ipynb   ← EDA with real LMRC data
│   └── 05_final_analysis.ipynb  ← Model training and evaluation
├── data/
│   ├── build_dataset.py          ← Downloads real LMRC data from S3
│   └── packages_validation.csv  ← 3,559 packages
├── ml/
│   └── random_forest_model.pkl  ← Trained model
├── scripts/
│   └── generate_charts.py       ← EDA chart generation
├── agents_crew.py               ← CrewAI agent definitions
├── train_model.py               ← Model training script
└── requirements.txt
```

---

## Setup

```bash
pip install -r requirements.txt
python data/build_dataset.py
python scripts/generate_charts.py
jupyter notebook notebooks/05_final_analysis.ipynb
```

---

## Academic Context

This project was submitted as the Week 12 Final Portfolio Project for the Correlation One Data Analytics (DANA) program.

Claude (Anthropic) was used as a writing and editing assistant for the academic documents. All technical work, analytical decisions, and findings are the author's own.

---

## Tools

| Layer | Technology |
|---|---|
| Language | Python 3.9+ |
| ML Model | scikit-learn RandomForestClassifier |
| Imbalance | imbalanced-learn (SMOTE) |
| Agents | CrewAI |
| Data | Amazon LMRC 2021 (public S3) |
| Notebooks | Jupyter |
| Visualization | matplotlib, seaborn |

---

*Built by Wagner Alexandre Campos | Correlation One DANA W12 | April 2026*
