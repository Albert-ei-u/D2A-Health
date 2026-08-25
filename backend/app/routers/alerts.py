from fastapi import APIRouter

from app.models import Alert
from app.services.alert_engine import generate_alerts
from app.services.dataset_store import get_active_patient_records
from app.services.synthetic_data import build_environmental_signals

router = APIRouter()


@router.get("", response_model=list[Alert])
def list_alerts() -> list[Alert]:
    return generate_alerts(get_active_patient_records(), build_environmental_signals())
