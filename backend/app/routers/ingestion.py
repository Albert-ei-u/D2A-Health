from fastapi import APIRouter, File, UploadFile

from app.models import IngestionResult
from app.services.data_ingestion import parse_patient_csv

router = APIRouter()


@router.post("/patient-csv", response_model=IngestionResult)
async def ingest_patient_csv(file: UploadFile = File(...)) -> IngestionResult:
    content = (await file.read()).decode("utf-8-sig")
    return parse_patient_csv(content)
