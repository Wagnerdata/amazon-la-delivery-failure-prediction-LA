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
│   └── packages_validation.csv # Validation set (5 routes)
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

2. **Rebuild the dataset (requires AWS S3 access):**
   ```bash
   python data/build_dataset.py
   ```

3. **Train the model:**
   ```bash
   python train_model.py
   ```

4. **Launch the dashboard:**
   ```bash
   streamlit run dashboard/dashboard.py
   ```

---

## 👨‍💻 Author
**Wagner Alexandre Campos**  
Data Analyst | Correlation One DANA Final Portfolio  
April 2026

---

## ⚖️ License
MIT License
