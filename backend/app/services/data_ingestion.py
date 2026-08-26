import csv
from io import StringIO

from pydantic import ValidationError

from app.models import IngestionResult, PatientRecord

REQUIRED_COLUMNS = {
    "record_id",
    "facility",
    "district",
    "week",
    "age_group",
    "condition",
    "visits",
    "admissions",
    "avg_wait_minutes",
}
OPTIONAL_COORDINATE_COLUMNS = {"latitude", "longitude"}


def parse_patient_csv(content: str) -> IngestionResult:
    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames:
        return IngestionResult(
            accepted_records=0,
            rejected_records=0,
            records=[],
            errors=["CSV file is empty or missing a header row."],
            active_data_source="synthetic",
        )

    missing_columns = sorted(REQUIRED_COLUMNS - set(reader.fieldnames))
    if missing_columns:
        return IngestionResult(
            accepted_records=0,
            rejected_records=0,
            records=[],
            errors=[f"Missing required columns: {', '.join(missing_columns)}."],
            active_data_source="synthetic",
        )

    records: list[PatientRecord] = []
    errors: list[str] = []
    seen_record_ids: set[str] = set()

    for row_number, row in enumerate(reader, start=2):
        try:
            record_id = _required_text(row.get("record_id"), "record_id")
            if record_id in seen_record_ids:
                raise ValueError(f"duplicate record_id '{record_id}'")
            seen_record_ids.add(record_id)

            facility = _required_text(row.get("facility"), "facility")
            district = _required_text(row.get("district"), "district")
            week = _required_text(row.get("week"), "week")
            age_group = _required_text(row.get("age_group"), "age_group")
            condition = _required_text(row.get("condition"), "condition")
            visits = int(row["visits"])
            admissions = int(row["admissions"])
            avg_wait_minutes = int(row["avg_wait_minutes"])
            if admissions > visits:
                raise ValueError("admissions cannot exceed visits")

            latitude = _optional_float(row.get("latitude"))
            longitude = _optional_float(row.get("longitude"))
            records.append(
                PatientRecord(
                    record_id=record_id,
                    facility=facility,
                    district=district,
                    week=week,
                    age_group=age_group,
                    condition=condition,
                    visits=visits,
                    admissions=admissions,
                    avg_wait_minutes=avg_wait_minutes,
                    latitude=latitude,
                    longitude=longitude,
                )
            )
        except (TypeError, ValueError, ValidationError) as error:
            errors.append(f"Row {row_number}: {error}")

    return IngestionResult(
        accepted_records=len(records),
        rejected_records=len(errors),
        records=records,
        errors=errors,
        active_data_source="csv_upload" if records else "synthetic",
    )


def _optional_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    return float(value)


def _required_text(value: str | None, field_name: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be blank")
    return cleaned
