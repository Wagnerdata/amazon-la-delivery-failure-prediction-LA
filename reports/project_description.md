# Project Description: Delivery Failure Prediction for Amazon LA Last-Mile Logistics

**Program:** Correlation One — Data Analytics (DANA), Week 12 Final Portfolio Project  
**Author:** Data Analytics Candidate  
**Date:** April 2026  
**Domain:** E-commerce Logistics / Last-Mile Delivery Operations

---

## 1. Industry Overview

Amazon LA operates one of the most complex last-mile delivery networks in the western United States. Since launching operations inLos Angeles in 2011, Amazon has expanded to serve millions of customers across the peninsula and the Balearic and Canary Islands. The Spanish logistics landscape presents unique operational challenges:

- **Fragmented urban geography**: Dense city centers (Los Angeles, Los Angeles, Valencia) co-exist with spread-out suburban and rural areas requiring varied routing strategies.
- **Multi-carrier dependency**: Amazon LA relies on Amazon Logistics (carrier_A), SEUR (carrier_B), DHL (carrier_C), and Correos (carrier_D) — each with different SLA profiles, technology maturity, and geographic coverage.
- **Seasonal and weather volatility**: Mediterranean climate brings flooding events, summer heat, and Levante winds that disrupt delivery operations in coastal regions.
- **Regulatory constraints**: Spanish labor laws (colectivo de transportistas) and municipal access restrictions (Los Angeles Central ZBE, Los Angeles Superilles) add operational constraints not present in other markets.

Last-mile delivery represents approximately 28–40% of total supply chain cost and is the primary touchpoint defining customer experience. A single failed delivery attempt inLos Angeles costs Amazon an estimated **$6–12** in redelivery cost, plus negative downstream effects on Customer Promise (DEA — Delivery Experience Accuracy) and Net Promoter Score (NPS).

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

The analysis uses a synthetic but operationally realistic dataset of **7,500 package delivery records** (5,000 train / 1,500 validation / 1,000 test), generated to reflect actual Amazon LA operational distributions.

| Variable | Type | Description |
|---|---|---|
| `package_id` | string | Unique package identifier (PKG-ES-XXXXXXX) |
| `package_type` | categorical | standard, high_value, fragile, locker, large |
| `shift` | categorical | Delivery shift: morning, afternoon, night |
| `carrier` | categorical | carrier_A (Amazon Logistics), B (SEUR), C (DHL), D (Correos) |
| `route_distance_km` | numeric | Route distance in kilometers (2–85 km) |
| `packages_in_route` | numeric | Total packages in the driver's route (15–120) |
| `double_scan` | binary | Scan error flag — package scanned twice or out of sequence |
| `locker_issue` | binary | Locker unavailable or full at dispatch time |
| `damaged_on_arrival` | binary | Package arrived at FC with visible damage |
| `weather_risk` | categorical | Weather risk level: low, medium, high |
| `cr_number_missing` | binary | Customer reference number absent from shipment record |
| `days_in_fc` | numeric | Days the package spent in the fulfillment center (0–12) |
| `delivery_failed` | binary | **TARGET**: 1 = delivery failed, 0 = delivered successfully |

**Overall failure rate: ~19.4%** across the training dataset — consistent with Amazon LA last-mile operational benchmarks.

---

## 4. Why This Problem Matters: Business Value

### Financial Impact
- **~19.4% failure rate** across 7,500 packages → ~1,455 failed deliveries in this sample
- At **$8 average cost per failed delivery attempt** (redelivery + customer service), this represents **~$11,640 in avoidable cost** in this sample alone
- Amazon LA processes millions of packages annually; a 2–3% failure rate reduction at scale translates to **millions of euros** in operational savings

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
