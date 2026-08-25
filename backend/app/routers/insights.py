from fastapi import APIRouter

from app.models import Insight
from app.services.dataset_store import get_active_patient_records
from app.services.insight_engine import generate_insights
from app.services.synthetic_data import build_environmental_signals

router = APIRouter()


@router.get("", response_model=list[Insight])
def list_insights() -> list[Insight]:
    return generate_insights(get_active_patient_records(), build_environmental_signals())
