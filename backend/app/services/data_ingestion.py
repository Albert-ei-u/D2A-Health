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
        )

    missing_columns = sorted(REQUIRED_COLUMNS - set(reader.fieldnames))
    if missing_columns:
        return IngestionResult(
            accepted_records=0,
            rejected_records=0,
            records=[],
            errors=[f"Missing required columns: {', '.join(missing_columns)}."],
        )

    records: list[PatientRecord] = []
    errors: list[str] = []

    for row_number, row in enumerate(reader, start=2):
        try:
            latitude = _optional_float(row.get("latitude"))
            longitude = _optional_float(row.get("longitude"))
            records.append(
                PatientRecord(
                    record_id=row["record_id"],
                    facility=row["facility"],
                    district=row["district"],
                    week=row["week"],
                    age_group=row["age_group"],
                    condition=row["condition"],
                    visits=int(row["visits"]),
                    admissions=int(row["admissions"]),
                    avg_wait_minutes=int(row["avg_wait_minutes"]),
                    latitude=latitude,
                    longitude=longitude,
                )
            )
        except (ValueError, ValidationError) as error:
            errors.append(f"Row {row_number}: {error}")

    return IngestionResult(
        accepted_records=len(records),
        rejected_records=len(errors),
        records=records,
        errors=errors,
    )


def _optional_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    return float(value)
