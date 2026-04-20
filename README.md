# Amazon LA — Last-Mile Delivery Failure Prediction

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![CrewAI](https://img.shields.io/badge/CrewAI-Agents-6B48FF)](https://www.crewai.com/)
[![Anthropic Claude](https://img.shields.io/badge/Claude-Sonnet_4.6-CC6B49)](https://www.anthropic.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_svg)](https://amazon-la-delivery-failure-prediction-la-roqisrmljj3rr9efltfzy.streamlit.app/)

End-to-end predictive system for Amazon last-mile logistics risk detection, built on the official **Amazon LMRC 2018** dataset (MIT CTL). Combines a tuned Random Forest classifier with a **FastAPI** REST layer, **CrewAI + Claude** agentic analysis, and a premium **Streamlit** operations dashboard — fully containerised with Docker Compose.

---

## Live Dashboard

**[→ Amazon LA Last-Mile Command Center](https://amazon-la-delivery-failure-prediction-la-roqisrmljj3rr9efltfzy.streamlit.app/)**

---

## Key Results

| Metric | Value |
|---|---|
| Model | Random Forest + SMOTE |
| AUC-ROC | **0.799** |
| Recall | **87.5%** |
| Precision | ~12% (real-world 140:1 imbalance) |
| Est. saving / flagged failure | **$17.50** |
| Dataset | 3,559 shipments · 15 LA routes |

---

## Architecture

```
┌──────────────┐     REST      ┌──────────────┐
│  Streamlit   │ ──────────── │   FastAPI    │
│  Dashboard   │   :8503       │   API        │  :8002
│  (port 8503) │               │  /predict    │
└──────────────┘               │  /analyze ──┐│
                                └─────────────┘│
                    ┌──────────────────────────┘
                    │  CrewAI Agent (Anthropic Claude)
                    │  tool_operational_analysis()
                    └──────────────────────────────
┌──────────────┐
│    Redis     │  :6379 — prediction caching
└──────────────┘
```

---

## Quick Start — Docker

> Requires: Docker Desktop 24+ with Compose v2

```bash
# 1. Clone
git clone https://github.com/Wagnerdata/amazon-la-delivery-failure-prediction-LA.git
cd amazon-la-delivery-failure-prediction-LA

# 2. Configure secrets
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Build & run all services
docker compose up --build

# Services:
#   API       →  http://localhost:8002
#   Dashboard →  http://localhost:8503
#   API docs  →  http://localhost:8002/docs
```

To run only the API (no dashboard):
```bash
docker compose up redis api
```

To rebuild after dependency changes:
```bash
docker compose build --no-cache && docker compose up
```

---

## API Reference

Base URL: `http://localhost:8002`

### `GET /health`
Service health check and model-load status.

### `GET /metrics`
Returns trained model metrics (AUC-ROC, recall, precision).

### `POST /predict`
Score a delivery package with the Random Forest model.

```bash
curl -X POST http://localhost:8002/predict \
  -H "Content-Type: application/json" \
  -d '{
    "carrier": "carrier_D",
    "shift": "morning",
    "package_type": "high_value",
    "route_distance_km": 65,
    "packages_in_route": 90,
    "double_scan": 1,
    "short_service_time": 0,
    "cr_number_missing": 1
  }'
```

Response:
```json
{
  "failure_probability": 0.6241,
  "risk_level": "HIGH",
  "model_auc": 0.799
}
```

### `POST /analyze`
CrewAI + Claude agentic analysis with operational flags and LLM recommendations.

```bash
curl -X POST http://localhost:8002/analyze \
  -H "Content-Type: application/json" \
  -d '{"carrier":"carrier_D","shift":"morning","package_type":"high_value","route_distance_km":65,"packages_in_route":90,"double_scan":1,"short_service_time":0,"cr_number_missing":1}'
```

---

## Project Structure

```
delivery-failure-prediction/
├── api/
│   └── main.py               # FastAPI app — /predict, /analyze, /health
├── dashboard/
│   └── dashboard.py          # Streamlit premium operations dashboard
├── artifacts/
│   └── delivery_model.pkl    # Serialised RF model + encoders + metrics
├── data/
│   ├── packages_train.csv
│   └── packages_validation.csv
├── sql/
│   ├── eda_queries.sql
│   └── eda_results.txt
├── agents_crew.py             # Operational flag analysis tool (CrewAI-ready)
├── train_model.py             # Model training & serialisation pipeline
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

---

## Dataset

Built from the **Amazon Last Mile Routing Research Challenge (2021)**, conducted with the **MIT Center for Transportation & Logistics**:

- **Scope:** 15 real delivery routes in Los Angeles, CA (July 2018)
- **Volume:** 3,559 individual shipments
- **Class imbalance:** ~140:1 (success vs. failure) — handled with SMOTE
- **Features:** carrier, shift, package type, route distance, route load, operational flags

---

## Machine Learning Pipeline

1. **Feature engineering** — distance binning, binary operational flags
2. **Imbalance handling** — SMOTE oversampling + class-weight balancing
3. **Model** — Random Forest (`n_estimators=200`, `max_depth=10`)
4. **Threshold optimisation** — tuned for recall (≥ 87.5%) to minimise missed failures
5. **Serialisation** — model + label encoders + live metrics saved to `.pkl`

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes (for `/analyze`) | Claude API key from console.anthropic.com |
| `REDIS_URL` | No | Defaults to `redis://redis:6379` in Compose |
| `MODEL_PATH` | No | Defaults to `artifacts/delivery_model.pkl` |

---

## Author

**Wagner Alexandre Campos** — Senior Data Analyst / Logistics Specialist  
Portfolio project for **Correlation One DANA Program** (Week 12 Final).  
Background in Amazon Debrief Operations and Predictive Logistics.

---

## License

Distributed under the MIT License.
