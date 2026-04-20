"""FastAPI prediction and CrewAI analysis service for Amazon LA delivery risk."""
from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

MODEL_PATH = Path(os.getenv("MODEL_PATH", "artifacts/delivery_model.pkl"))

app = FastAPI(
    title="Amazon LA — Delivery Failure Prediction API",
    version="1.0.0",
    description="Last-mile logistics risk scoring powered by Random Forest + CrewAI agents",
)

_artifact: dict[str, Any] | None = None


@app.on_event("startup")
async def _load_model() -> None:
    global _artifact
    if MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as fh:
            _artifact = pickle.load(fh)


# ── Schema ────────────────────────────────────────────────────────────────────

class PackageInput(BaseModel):
    carrier: str = Field("carrier_A", examples=["carrier_A", "carrier_B", "carrier_C", "carrier_D"])
    shift: str = Field("morning", examples=["morning", "afternoon"])
    package_type: str = Field("standard", examples=["standard", "high_value"])
    route_distance_km: float = Field(25.0, ge=0)
    packages_in_route: int = Field(75, ge=1)
    double_scan: int = Field(0, ge=0, le=1)
    short_service_time: int = Field(0, ge=0, le=1)
    cr_number_missing: int = Field(0, ge=0, le=1)


class PredictionOut(BaseModel):
    failure_probability: float
    risk_level: str
    model_auc: float | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {"status": "ok", "model_loaded": _artifact is not None}


@app.get("/metrics", tags=["ops"])
async def model_metrics() -> dict:
    if _artifact is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return _artifact.get("metrics", {})


@app.post("/predict", response_model=PredictionOut, tags=["prediction"])
async def predict(pkg: PackageInput) -> PredictionOut:
    if _artifact is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    model = _artifact["model"]
    encoders = _artifact["encoders"]

    d = pkg.route_distance_km
    dist_bin = 0 if d <= 15 else 1 if d <= 30 else 2 if d <= 50 else 3 if d <= 70 else 4

    row = [
        encoders["carrier"].transform([pkg.carrier])[0],
        encoders["shift"].transform([pkg.shift])[0],
        encoders["package_type"].transform([pkg.package_type])[0],
        dist_bin,
        pkg.packages_in_route,
        pkg.double_scan,
        pkg.short_service_time,
        pkg.cr_number_missing,
    ]
    prob = float(model.predict_proba([row])[0][1])
    risk = "HIGH" if prob >= 0.50 else "MEDIUM" if prob >= 0.16 else "LOW"

    return PredictionOut(
        failure_probability=round(prob, 4),
        risk_level=risk,
        model_auc=_artifact.get("metrics", {}).get("auc_roc"),
    )


@app.post("/analyze", tags=["agents"])
async def analyze(pkg: PackageInput) -> dict:
    """Run CrewAI + Claude analysis for a delivery package."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    try:
        from crewai import Agent, Crew, LLM, Task
    except ImportError:
        raise HTTPException(status_code=503, detail="crewai not installed")

    from agents_crew import tool_operational_analysis

    op_flags = tool_operational_analysis(pkg.model_dump())

    llm = LLM(model="anthropic/claude-sonnet-4-6", api_key=api_key)

    analyst = Agent(
        role="Logistics Risk Analyst",
        goal="Identify delivery failure risks and provide actionable operational recommendations",
        backstory=(
            "Senior analyst at Amazon's last-mile operations center. "
            "Expert in carrier performance, route optimization, and SLA risk mitigation."
        ),
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=(
            f"Analyze this delivery package and produce a concise operational report.\n\n"
            f"Package: {pkg.model_dump()}\n"
            f"Operational flags: {op_flags}\n\n"
            "Output: 1) Risk level 2) Root causes 3) Top 2 recommendations. Max 150 words."
        ),
        expected_output="Structured risk report under 150 words.",
        agent=analyst,
    )

    crew = Crew(agents=[analyst], tasks=[task], verbose=False)
    result = crew.kickoff()

    return {"operational_flags": op_flags, "ai_analysis": str(result)}
