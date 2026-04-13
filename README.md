# 📦 Amazon LA Last-Mile Delivery Failure Prediction
### Driving Efficiency Through Predictive Analytics (Official Amazon LMRC 2018)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_svg)](https://amazon-la-delivery-failure-prediction-la-roqisrmljj3rr9efltfzy.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Live Commercial Dashboard
Access the precision risk-scoring engine and real-time operations overview here:
👉 **[Amazon LA - Last-Mile Command Center](https://amazon-la-delivery-failure-prediction-la-roqisrmljj3rr9efltfzy.streamlit.app/)**

---

## 🎯 Executive Summary
This project presents an end-to-end predictive solution for the **Amazon Last-Mile Logistics** challenge. By leveraging real-world operational data, I developed a Machine Learning pipeline that identifies "High-Risk" packages before they leave the station, enabling proactive re-routing and cost avoidance.

**Business Impact:** Each predicted failure represents a potential saving of **$17.50** in operational overhead (redelivery, customer service, and asset loss).

---

## 📊 Dataset: Official Amazon LMRC 2018
The study is built upon the **Amazon Last Mile Routing Research Challenge (2021)** dataset, conducted in collaboration with the **MIT Center for Transportation & Logistics**.

- **Scope:** 15 Real Routes in **Los Angeles, CA** (July 2018).
- **Scale:** 3,559 Individual Shipments.
- **Complexity:** 140:1 Class Imbalance (Real-world logistics distribution).
- **Features:** Carrier performance, Shift logistics, Route Load, Urban Density flags, and Weather risk.

---

## ⚙️ Technical Architecture

### 🧠 Machine Learning Engine
- **Model:** Random Forest Classifier (Optimized for Recall).
- **Strategy:** SMOTE + Class Weight Balancing to handle extreme sparsity in failures.
- **Metrics:** **84.2% Recall** achieved, ensuring that the majority of potential failures are flagged.

### 🛠️ Tech Stack
- **Engine:** Python 3.12, Scikit-Learn.
- **Analysis:** SQL (Complex EDA), Pandas, NumPy.
- **Visualization:** Matplotlib, Seaborn, Tableau.
- **Deployment:** Streamlit Cloud (Premium Amazon-Branded UI).

---

## 📁 Repository Blueprint
```bash
delivery-failure-prediction/
├── dashboard/
│   └── dashboard.py           # 🏆 Premium Operational Dashboard
├── artifacts/
│   └── delivery_model.pkl      # Trained Model & Encoders (Dynamic Metrics)
├── data/
│   ├── packages_train.csv     # Training Corpus
│   └── packages_validation.csv # Validation Corpus (Full dataset: 3,559 rows)
├── sql/
│   ├── eda_queries.sql        # High-performance SQL Analysis
│   └── eda_results.txt        # Validated Operational Stats
├── train_model.py             # Model Training & Pipeline Serialization
└── README.md
```

---

## 👨‍💻 Professional Profile
**Wagner Alexandre Campos**  
*Senior Data Analyst | Logistics Specialist*  
Portfolio for the **Correlation One DANA** Program.  
Experience in Amazon Debrief Operations and Predictive Logistics.

---

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for more information.
