from fastapi import APIRouter

from app.models import EnvironmentalSignal, PatientRecord
from app.services.dataset_store import get_active_patient_records
from app.services.synthetic_data import build_environmental_signals

router = APIRouter()


@router.get("", response_model=list[PatientRecord])
def list_records() -> list[PatientRecord]:
    return get_active_patient_records()


@router.get("/environment", response_model=list[EnvironmentalSignal])
def list_environmental_signals() -> list[EnvironmentalSignal]:
    return build_environmental_signals()
