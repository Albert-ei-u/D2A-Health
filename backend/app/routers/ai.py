from dataclasses import asdict

from fastapi import APIRouter, Header

from app.models import AIPipelineResponse
from app.services.ai_pipeline import run_ai_pipeline
from app.services.dataset_store import active_data_source, require_user_dataset

router = APIRouter()


@router.get("/pipeline", response_model=AIPipelineResponse)
def get_ai_pipeline(x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> AIPipelineResponse:
    records = require_user_dataset(x_user_email)
    result = run_ai_pipeline(records, [])

    return AIPipelineResponse(
        active_data_source=active_data_source(x_user_email),
        alerts=result.alerts,
        insights=result.insights,
        anomalies=[asdict(signal) for signal in result.anomalies],
        forecast=asdict(result.forecast),
        trace=result.trace,
    )
