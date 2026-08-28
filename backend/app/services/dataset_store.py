from app.models import PatientRecord
from app.db import SessionLocal, init_db
from app.db_models import UserPatientRecordRow, UserRow
from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.exc import SQLAlchemyError

_uploaded_patient_records: dict[str, list[PatientRecord]] = {}


def normalize_email(email: str | None) -> str:
    return (email or "").strip().lower()


def get_active_patient_records(user_email: str | None = None) -> list[PatientRecord]:
    """Return only this user's uploaded data."""
    email = normalize_email(user_email)
    if not email:
        return []
    if email in _uploaded_patient_records:
        return list(_uploaded_patient_records[email])

    try:
        init_db()
        with SessionLocal() as session:
            rows = session.scalars(
                select(UserPatientRecordRow).where(UserPatientRecordRow.owner_email == email)
            ).all()
            records = [_to_patient_record(row) for row in rows]
            if records:
                _uploaded_patient_records[email] = records
            return records
    except SQLAlchemyError:
        return []


def replace_uploaded_patient_records(records: list[PatientRecord], user_email: str) -> None:
    email = normalize_email(user_email)
    _uploaded_patient_records[email] = list(records)

    try:
        init_db()
        with SessionLocal.begin() as session:
            session.execute(delete(UserPatientRecordRow).where(UserPatientRecordRow.owner_email == email))
            session.add_all(
                UserPatientRecordRow(owner_email=email, **record.model_dump()) for record in records
            )
    except SQLAlchemyError:
        pass


def append_uploaded_patient_records(records: list[PatientRecord], user_email: str) -> tuple[list[PatientRecord], list[str]]:
    email = normalize_email(user_email)
    existing = get_active_patient_records(email)
    existing_ids = {record.record_id for record in existing}
    accepted = [record for record in records if record.record_id not in existing_ids]
    errors = [f"Duplicate record_id '{record.record_id}' already exists." for record in records if record.record_id in existing_ids]
    if accepted:
        replace_uploaded_patient_records(existing + accepted, email)
        mark_user_dataset_ready(email)
    return accepted, errors


def clear_uploaded_patient_records(user_email: str | None = None) -> None:
    """Clear one user's records, or all test records when no owner is supplied."""
    if user_email is None:
        _uploaded_patient_records.clear()
        try:
            init_db()
            with SessionLocal.begin() as session:
                session.execute(delete(UserPatientRecordRow))
        except SQLAlchemyError:
            pass
        return

    email = normalize_email(user_email)
    _uploaded_patient_records.pop(email, None)

    try:
        init_db()
        with SessionLocal.begin() as session:
            session.execute(delete(UserPatientRecordRow).where(UserPatientRecordRow.owner_email == email))
    except SQLAlchemyError:
        pass


def active_data_source(user_email: str | None = None) -> str:
    return "csv_upload" if get_active_patient_records(user_email) else "none"


def require_user_dataset(user_email: str | None) -> list[PatientRecord]:
    email = normalize_email(user_email)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in is required.")
    records = get_active_patient_records(email)
    if not records:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Upload your health center CSV before accessing analytics.")
    return records


def mark_user_dataset_ready(email: str) -> None:
    try:
        init_db()
        with SessionLocal.begin() as session:
            session.execute(
                update(UserRow)
                .where(UserRow.email == email.strip().lower())
                .values(dataset_ready=True)
            )
    except SQLAlchemyError:
        pass


def _to_patient_record(row: UserPatientRecordRow) -> PatientRecord:
    return PatientRecord.model_validate(
        {
            "record_id": row.record_id,
            "facility": row.facility,
            "district": row.district,
            "village": row.village,
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
