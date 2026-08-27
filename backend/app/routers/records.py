from fastapi import APIRouter, Header

from app.models import EnvironmentalSignal, FacilityLocation, PatientRecord
from app.services.analytics import facility_locations
from app.services.dataset_store import active_data_source, require_user_dataset

router = APIRouter()


@router.get("", response_model=list[PatientRecord])
def list_records(x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> list[PatientRecord]:
    return require_user_dataset(x_user_email)


@router.get("/locations", response_model=list[FacilityLocation])
def list_facility_locations(x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> list[FacilityLocation]:
    return facility_locations(require_user_dataset(x_user_email), active_data_source(x_user_email))


@router.get("/environment", response_model=list[EnvironmentalSignal])
def list_environmental_signals(x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> list[EnvironmentalSignal]:
    require_user_dataset(x_user_email)
    return []
