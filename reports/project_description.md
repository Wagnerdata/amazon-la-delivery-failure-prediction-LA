# Project Description: Delivery Failure Prediction for Amazon LA Last-Mile Logistics

**Program:** Correlation One — Data Analytics (DANA), Week 12 Final Portfolio Project  
**Author:** Data Analytics Candidate  
**Date:** April 2026  
**Domain:** E-commerce Logistics / Last-Mile Delivery Operations

---

## 1. Industry Overview

Amazon LA operates one of the most complex last-mile delivery networks in Southern California. Since launching operations in Los Angeles in 2011, Amazon has expanded to serve millions of customers across the Greater LA Basin and surrounding counties. The Southern California logistics landscape presents unique operational challenges:

- **Densely populated urban geography**: High-traffic city centers (Downtown LA, Santa Monica, Long Beach) co-exist with vast suburban sprawl requiring varied routing strategies.
- **Multi-carrier dependency**: Amazon LA relies on Amazon Logistics (carrier_A), Regional Hub Partners (carrier_B), Express Hub Courier (carrier_C), and Local Courier Services (carrier_D) — each with different SLA profiles, technology maturity, and geographic coverage.
- **Seasonal and weather volatility**: Southern California's climate brings intense July heatwaves, Santa Ana wind events, and seasonal marine layer fog that can disrupt morning delivery operations.
- **Regulatory and access constraints**: Local municipal access restrictions (LA Central traffic zones) and secured building protocols (apartment lobbies, complex gate codes) add operational constraints common in dense urban markets.

Last-mile delivery represents approximately 28–40% of total supply chain cost and is the primary touchpoint defining customer experience. A single failed delivery attempt in Los Angeles costs Amazon an estimated **$6–12** in redelivery cost, plus negative downstream effects on Customer Promise (DEA — Delivery Experience Accuracy) and Net Promoter Score (NPS).

---

## 2. Problem Statement

**Can we predict whether a package will fail to be delivered before the delivery attempt is made?**

Currently, Amazon LA logistics operations respond *reactively* to delivery failures — analyzing failed attempts after the fact through DPMO (Defects Per Million Opportunities) reporting cycles. This reactive approach means:

1. Failed delivery costs are already incurred before intervention is possible.
2. Customer experience scores (VOC — Voice of Customer) suffer before corrective actions can be taken.
3. Route optimization decisions are made without failure probability information.

This project builds a **proactive, pre-dispatch prediction model** that estimates the probability of a delivery failure given known package attributes and operational conditions at dispatch time. With this model, Amazon operations managers can:

- Flag high-risk packages for manual review before dispatch.
- Assign high-risk packages to higher-performing carriers.
- Adjust route loads to reduce overloaded drivers on high-risk days.
- Prioritize locker and address verification for packages with missing customer references.

---

## 3. Dataset Description

The analysis uses a real dataset of **3,559 package delivery records** (2,384 train / 1,175 validation), reflecting actual Amazon LA operational distributions in July 2018.

| Variable | Type | Description |
|---|---|---|
| `package_id` | string | Unique package identifier (PackageID_UUID) |
| `package_type` | categorical | standard, high_value, fragile, locker, large |
| `shift` | categorical | Delivery shift: morning, afternoon, night |
| `carrier` | categorical | carrier_A (Amazon Logistics), B (Regional Hub), C (Express Hub), D (Local Courier) |
| `route_distance_km` | numeric | Route distance in kilometers (2–85 km) |
| `packages_in_route` | numeric | Total packages in the driver's route (15–120) |
| `double_scan` | binary | Scan error flag — package scanned twice or out of sequence |
| `locker_issue` | binary | Locker unavailable or full at dispatch time |
| `damaged_on_arrival` | binary | Package arrived at FC with visible damage |
| `weather_risk` | categorical | Weather risk level: low, medium, high |
| `cr_number_missing` | binary | Customer reference number absent from shipment record |
| `days_in_fc` | numeric | Days the package spent in the fulfillment center (0–12) |
| `delivery_failed` | binary | **TARGET**: 1 = delivery failed, 0 = delivered successfully |

**Overall failure rate: ~0.70%** across the dataset — consistent with Amazon LA last-mile operational benchmarks for the LMRC research dataset.

---

## 4. Why This Problem Matters: Business Value

### Financial Impact
- **~0.70% failure rate** across 3,559 packages → 25 failed deliveries in this sample
- At **$17 average cost per failed delivery attempt** (redelivery + customer service), this represents **~$425 in direct avoidable cost** in this sample alone
- Amazon LA processes millions of packages annually; a fractional failure rate reduction at scale translates to **millions of dollars** in operational savings

### Amazon KPI Impact
| Metric | How This Project Addresses It |
|---|---|
| **DPMO** (Defects Per Million Opportunities) | Prediction model directly reduces delivery defects |
| **DEA** (Delivery Experience Accuracy) | Proactive intervention improves promise keeping |
| **VOC** (Voice of Customer) | Fewer failed deliveries = fewer negative reviews and contacts |
| **OTIF** (On-Time In-Full) | Model flags routes/carriers at risk of missing SLAs |

### Strategic Value
This model serves as a foundation for a **real-time scoring system** that could integrate with Amazon's internal WMS (Warehouse Management System) and TMS (Transportation Management System), scoring each package at dispatch and routing it to the optimal carrier and shift.

---

## 5. Analytical Approach

This project applies the full data analytics lifecycle:

1. **Data Curation**: Schema validation, missing value analysis, outlier detection, and feature encoding
2. **Exploratory Data Analysis (EDA)**: Univariate and bivariate analysis revealing failure patterns by carrier, shift, weather, and package type
3. **Predictive Modeling**: RandomForestClassifier (sklearn) with balanced class weights, achieving AUC-ROC of 0.71 on the validation set
4. **Dashboard**: Interactive Streamlit application enabling operations managers to explore failure patterns and score individual packages in real time
5. **Business Recommendations**: Actionable insights for Amazon LA operations and transportation teams

---

*This project was completed as part of the Correlation One Data Analytics (DANA) program, Week 12 Final Portfolio Project.*
