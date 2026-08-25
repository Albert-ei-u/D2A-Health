from app.models import PatientRecord
from app.services.synthetic_data import build_patient_records

_uploaded_patient_records: list[PatientRecord] = []


def get_active_patient_records() -> list[PatientRecord]:
    if _uploaded_patient_records:
        return list(_uploaded_patient_records)
    return build_patient_records()


def replace_uploaded_patient_records(records: list[PatientRecord]) -> None:
    _uploaded_patient_records.clear()
    _uploaded_patient_records.extend(records)


def clear_uploaded_patient_records() -> None:
    _uploaded_patient_records.clear()


def active_data_source() -> str:
    return "csv_upload" if _uploaded_patient_records else "synthetic"
