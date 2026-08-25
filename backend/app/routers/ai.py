from dataclasses import asdict

from fastapi import APIRouter

from app.models import AIPipelineResponse
from app.services.ai_pipeline import run_ai_pipeline
from app.services.synthetic_data import build_environmental_signals, build_patient_records

router = APIRouter()


@router.get("/pipeline", response_model=AIPipelineResponse)
def get_ai_pipeline() -> AIPipelineResponse:
    result = run_ai_pipeline(build_patient_records(), build_environmental_signals())

    return AIPipelineResponse(
        alerts=result.alerts,
        insights=result.insights,
        anomalies=[asdict(signal) for signal in result.anomalies],
        forecast=asdict(result.forecast),
        trace=result.trace,
    )
