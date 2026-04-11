# 💳 Credit Risk AI System — SME Default Prediction

> End-to-end credit risk platform: ML model predicts default probability for SMEs + autonomous AI agents analyze financial ratios and generate executive risk reports.

## Overview

This system predicts the **12-month default probability** for Small and Medium Enterprises (SMEs) using a Machine Learning model, then deploys **3 autonomous AI agents** (CrewAI) to analyze financial statements, interpret risk signals, and produce executive-ready credit reports.

---

## Architecture

```
Company ID
     │
     ▼
┌─────────────────┐      ┌──────────────────────────┐
│  FastAPI        │◄─────│  ML Model (Random Forest) │
│  /calcular_pd   │      │  Outputs: PD% + Risk Band  │
└────────┬────────┘      └──────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│           CrewAI Agent Crew             │
│  Agent 1: PD Model Specialist           │
│  Agent 2: Financial Ratio Analyst       │
│  Agent 3: Risk Orchestrator             │
└─────────────────┬───────────────────────┘
                  │
                  ▼
    Executive Credit Risk Report
                  │
                  ▼
       Streamlit Dashboard
```

---

## Features

- **ML Default Prediction**: 12-month probability of default (PD) with risk bands A / BBB / BB / B / CCC
- **Financial Ratio Analysis**: Liquidity, leverage, EBITDA margin, interest coverage, revenue growth
- **AI Agent Crew**: 3 specialized agents produce actionable executive credit reports
- **REST API**: FastAPI with `/calcular_pd` endpoint
- **Interactive Dashboard**: Streamlit with risk gauge, metrics and report visualization

---

## Risk Band Scale

| Band | PD Range | Risk Level |
|------|----------|-----------|
| A | ≤ 0.5% | Very Low |
| BBB | 0.5% – 1.5% | Low |
| BB | 1.5% – 3% | Medium |
| B | 3% – 7% | High |
| CCC | > 7% | Very High |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ML Model | scikit-learn (Random Forest) |
| API | FastAPI + Pydantic |
| AI Agents | CrewAI |
| Dashboard | Streamlit + Plotly |
| Data | pandas + numpy |

---

## Project Structure

```
credit-risk-ai-agents/
│
├── api_pd.py                    # FastAPI — default probability endpoint
├── agentes.py                   # CrewAI autonomous agents
├── app_streamlit.py             # Streamlit dashboard
│
├── datos/
│   ├── pd_validacion.csv        # Validation dataset
│   └── estados_financieros_validacion.csv
│
├── artefactos/
│   └── modelo_pd.pkl            # Trained ML model + scaler
│
├── requirements.txt
└── README.md
```

---

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add API key to .env
echo "OPENAI_API_KEY=sk-..." > .env

# 3. Start API
uvicorn api_pd:app --reload

# 4. Run dashboard
streamlit run app_streamlit.py
```

---

## API Endpoint

```
POST /calcular_pd
{"id_empresa": 42}

→ {
    "id_empresa": 42,
    "pd_12m": 0.0312,
    "banda_score": "B"
  }
```

---

## Key Financial Ratios Analyzed

| Ratio | Formula | Interpretation |
|-------|---------|----------------|
| Liquidity | Current Assets / Current Liabilities | ≥ 1.2 = healthy |
| Leverage | Total Liabilities / Equity | ≤ 3 = reasonable |
| EBITDA Margin | EBITDA / Revenue | > 10% = healthy |
| Interest Coverage | EBITDA / Interest Expense | > 3x = safe |
| Revenue Growth | YoY Revenue Change | > 0 = growing |

---

## Author

**Wagner Alexandre Campos**
Data Analyst | Credit Risk & Financial Intelligence
- 1.5 years Data Science & ML training (Google/Coursera, Correlation One)
- Stack: Python · FastAPI · CrewAI · scikit-learn · Streamlit · Plotly
- Projects: Logistics failure prediction + Credit risk AI system

---

## License

MIT License
