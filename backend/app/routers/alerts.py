from fastapi import APIRouter

from app.models import Alert
from app.services.alert_engine import generate_alerts
from app.services.synthetic_data import build_patient_records

router = APIRouter()


@router.get("", response_model=list[Alert])
def list_alerts() -> list[Alert]:
    return generate_alerts(build_patient_records())
