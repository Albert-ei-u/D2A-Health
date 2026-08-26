from fastapi import APIRouter

from app.models import EnvironmentalSignal, FacilityLocation, PatientRecord
from app.services.analytics import facility_locations
from app.services.dataset_store import active_data_source, get_active_patient_records
from app.services.synthetic_data import build_environmental_signals

router = APIRouter()


@router.get("", response_model=list[PatientRecord])
def list_records() -> list[PatientRecord]:
    return get_active_patient_records()


@router.get("/locations", response_model=list[FacilityLocation])
def list_facility_locations() -> list[FacilityLocation]:
    return facility_locations(get_active_patient_records(), active_data_source())


@router.get("/environment", response_model=list[EnvironmentalSignal])
def list_environmental_signals() -> list[EnvironmentalSignal]:
    return build_environmental_signals()
