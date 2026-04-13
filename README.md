# 📦 Amazon LA Last-Mile Delivery Failure Prediction

> Academic Project (Correlation One DANA) — Predicting delivery failures using the real-world Amazon Last Mile Routing Research Challenge (LMRC) dataset from Los Angeles (2018).

## Overview
This project focuses on predicting the probability that an Amazon package delivery will fail (delivery attempted but not completed) based on historical route data. The system uses a Machine Learning model (Random Forest) trained on real operational data to identify high-risk packages before dispatch.

---

## 📊 Dataset: Amazon LMRC 2018
The data is sourced from the **2021 Amazon Last Mile Routing Research Challenge**, containing real-world deliveries performed by Amazon drivers in **Los Angeles, CA** during **July 2018**.

- **Scope:** 15 Routes, 3,559 Packages.
- **Features:** 
  - Package type (Standard/High Value).
  - Delivery Shift (Morning/Afternoon/Night).
  - Carrier performance metrics.
  - Route distance (km).
  - Route density (packages per route).
  - Operational flags (Double scans, Locker issues, Missing references).
- **Target:** Delivery Failure (Proxy: `damaged_on_arrival` flag in raw data).

---

## ⚙️ Model Architecture
- **Classifier:** Random Forest (n_estimators=300, max_depth=8).
- **Handling Imbalance:** `class_weight='balanced'` to manage the 140:1 failure ratio.
- **Optimization:** Decision threshold tuned for maximum **Recall**, prioritizing the detection of potential failures.
- **Performance:** AUC-ROC ≈ 0.70.

---

## 📁 Project Structure
```
delivery-failure-prediction/
│
├── data/
│   ├── build_dataset.py       # Data extraction from Amazon S3 (Real 2018 data)
│   ├── packages_train.csv     # Training set (10 routes)
│   ├── packages_validation.csv # Validation set (5 routes)
│   └── Amazon_LA_Curated_Delivery_Dataset.xlsx # 🏆 Master Dataset for Portfolio
│
├── notebooks/
│   └── 05_final_analysis.ipynb # Core research and model experimentation
│
├── train_model.py             # Operational script for model training
├── agents_crew.py              # AI Agent tools for risk assessment
├── dashboard/
│   └── dashboard.py           # Streamlit operacional dashboard
│
├── artifacts/
│   └── delivery_model.pkl      # Trained model object
│
└── requirements.txt
```

---

## 🚀 Quickstart

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Access the Curated Data:**
   Open `data/Amazon_LA_Curated_Delivery_Dataset.xlsx` to view the full 3,559 records used in the study.

3. **Rebuild the dataset (requires AWS S3 access):**
   ```bash
   python data/build_dataset.py
   ```

4. **Train the model:**
   ```bash
   python train_model.py
   ```

5. **Launch the dashboard:**
   ```bash
   streamlit run dashboard/dashboard.py
   ```

---

## 📂 Deliverables Catalog

This project includes a suite of professional deliverables designed for executive stakeholders:

1.  **[01_Project_Description](file:///c:/Users/User/Correlation%20one%20Logistc%20Predict%20agent/delivery-failure-prediction/deliverables/01_project_description_FINAL.docx)**: Business context and operational problem definition.
2.  **[02_Project_Scoping](file:///c:/Users/User/Correlation%20one%20Logistc%20Predict%20agent/delivery-failure-prediction/deliverables/02_project_scoping_FINAL.docx)**: Strategic boundaries, KPIs, and success criteria.
3.  **[03_Data_Curation_Report](file:///c:/Users/User/Correlation%20one%20Logistc%20Predict%20agent/delivery-failure-prediction/deliverables/03_data_curation_FINAL.docx)**: Detailed data lineage, profiling, and cleaning logs.
4.  **[04_EDA_Executive_Summary](file:///c:/Users/User/Correlation%20one%20Logistc%20Predict%20agent/delivery-failure-prediction/deliverables/04_eda_FINAL.docx)**: Visual and SQL-based insights (Urban Density Paradox).
5.  **[05_Datafolio_Poster](file:///c:/Users/User/Correlation%20one%20Logistc%20Predict%20agent/delivery-failure-prediction/deliverables/05_datafolio.pptx)**: Single-slide conference-style presentation.
6.  **[07_Final_Technical_Report](file:///c:/Users/User/Correlation%20one%20Logistc%20Predict%20agent/delivery-failure-prediction/deliverables/07_final_report_FINAL.docx)**: Comprehensive summary of all methodology and ROI results.

---

## 👨‍💻 Author
**Wagner Alexandre Campos**  
Senior Data Analyst Candidate | Correlation One DANA Final Portfolio  
*Specialized in Amazon Last-Mile Logistics Efficiency*
April 2026

---

## ⚖️ License
MIT License
