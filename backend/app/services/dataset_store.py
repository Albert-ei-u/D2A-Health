from app.models import PatientRecord
from app.db import SessionLocal, init_db
from app.db_models import PatientRecordRow
from app.services.synthetic_data import build_patient_records
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

_uploaded_patient_records: list[PatientRecord] = []


def get_active_patient_records() -> list[PatientRecord]:
    if _uploaded_patient_records:
        return list(_uploaded_patient_records)

    try:
        init_db()
        with SessionLocal() as session:
            rows = session.scalars(select(PatientRecordRow)).all()
            if rows:
                records = [_to_patient_record(row) for row in rows]
                _uploaded_patient_records.extend(records)
                return records
    except SQLAlchemyError:
        pass

    return build_patient_records()


def replace_uploaded_patient_records(records: list[PatientRecord]) -> None:
    _uploaded_patient_records.clear()
    _uploaded_patient_records.extend(records)

    try:
        init_db()
        with SessionLocal.begin() as session:
            session.execute(delete(PatientRecordRow))
            session.add_all(PatientRecordRow(**record.model_dump()) for record in records)
    except SQLAlchemyError:
        pass


def clear_uploaded_patient_records() -> None:
    _uploaded_patient_records.clear()

    try:
        init_db()
        with SessionLocal.begin() as session:
            session.execute(delete(PatientRecordRow))
    except SQLAlchemyError:
        pass


def active_data_source() -> str:
    return "csv_upload" if get_active_patient_records() and _uploaded_patient_records else "synthetic"


def _to_patient_record(row: PatientRecordRow) -> PatientRecord:
    return PatientRecord.model_validate(
        {
            "record_id": row.record_id,
            "facility": row.facility,
            "district": row.district,
            "week": row.week,
            "age_group": row.age_group,
            "condition": row.condition,
            "visits": row.visits,
            "admissions": row.admissions,
            "avg_wait_minutes": row.avg_wait_minutes,
            "latitude": row.latitude,
            "longitude": row.longitude,
        }
    )
