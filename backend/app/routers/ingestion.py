from fastapi import APIRouter, File, Header, HTTPException, UploadFile, status

from app.models import IngestionResult
from app.services.data_ingestion import parse_patient_csv
from app.services.dataset_store import (
    active_data_source,
    append_uploaded_patient_records,
    clear_uploaded_patient_records,
    mark_user_dataset_ready,
    replace_uploaded_patient_records,
)

router = APIRouter()


@router.post("/patient-csv", response_model=IngestionResult)
async def ingest_patient_csv(
    file: UploadFile = File(...),
    user_email: str | None = Header(default=None, alias="X-User-Email"),
) -> IngestionResult:
    if not user_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in is required before uploading data.")
    content = (await file.read()).decode("utf-8-sig")
    result = parse_patient_csv(content)
    if result.records:
        replace_uploaded_patient_records(result.records, user_email)
        mark_user_dataset_ready(user_email)
        result.active_data_source = active_data_source(user_email)
    return result


@router.post("/patient-csv/append", response_model=IngestionResult)
async def append_patient_csv(
    file: UploadFile = File(...),
    user_email: str | None = Header(default=None, alias="X-User-Email"),
) -> IngestionResult:
    if not user_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in is required before uploading data.")
    content = (await file.read()).decode("utf-8-sig")
    result = parse_patient_csv(content)
    if result.records:
        accepted, duplicate_errors = append_uploaded_patient_records(result.records, user_email)
        result.records = accepted
        result.accepted_records = len(accepted)
        result.rejected_records += len(duplicate_errors)
        result.errors.extend(duplicate_errors)
        result.active_data_source = active_data_source(user_email)
    return result


@router.delete("/patient-csv")
def clear_patient_csv(user_email: str | None = Header(default=None, alias="X-User-Email")) -> dict[str, str]:
    if not user_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in is required.")
    clear_uploaded_patient_records(user_email)
    return {"status": "cleared", "active_data_source": "none"}
