from fastapi import APIRouter

from app.models import Insight
from app.services.insight_engine import generate_insights
from app.services.synthetic_data import build_environmental_signals, build_patient_records

router = APIRouter()


@router.get("", response_model=list[Insight])
def list_insights() -> list[Insight]:
    return generate_insights(build_patient_records(), build_environmental_signals())
