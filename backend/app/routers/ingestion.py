from fastapi import APIRouter, File, UploadFile

from app.models import IngestionResult
from app.services.data_ingestion import parse_patient_csv
from app.services.dataset_store import clear_uploaded_patient_records, replace_uploaded_patient_records

router = APIRouter()


@router.post("/patient-csv", response_model=IngestionResult)
async def ingest_patient_csv(file: UploadFile = File(...)) -> IngestionResult:
    content = (await file.read()).decode("utf-8-sig")
    result = parse_patient_csv(content)
    if result.records:
        replace_uploaded_patient_records(result.records)
    return result


@router.delete("/patient-csv")
def clear_patient_csv() -> dict[str, str]:
    clear_uploaded_patient_records()
    return {"status": "cleared", "active_data_source": "synthetic"}
