from app.models import EnvironmentalSignal, PatientRecord

WEEKS = ["2026-W19", "2026-W20", "2026-W21", "2026-W22", "2026-W23", "2026-W24"]
DISTRICTS = ["Gasabo", "Kicukiro", "Nyarugenge"]
CONDITIONS = ["Malaria", "Respiratory infection", "Diarrheal disease", "Hypertension"]
AGE_GROUPS = ["0-5", "6-17", "18-59", "60+"]


def build_patient_records() -> list[PatientRecord]:
    records: list[PatientRecord] = []
    counter = 1

    for week_index, week in enumerate(WEEKS):
        for district_index, district in enumerate(DISTRICTS):
            for condition_index, condition in enumerate(CONDITIONS):
                baseline = 18 + (district_index * 4) + (condition_index * 3)
                trend = week_index * (2 if condition in {"Malaria", "Respiratory infection"} else 1)
                spike = 24 if week == "2026-W24" and district == "Gasabo" and condition == "Malaria" else 0
                visits = baseline + trend + spike
                admissions = max(1, round(visits * (0.08 + condition_index * 0.01)))
                wait = 28 + district_index * 6 + week_index * 2 + (10 if visits > 45 else 0)

                records.append(
                    PatientRecord(
                        record_id=f"anon-{counter:04d}",
                        facility=f"{district} District Hospital",
                        district=district,
                        week=week,
                        age_group=AGE_GROUPS[(week_index + condition_index) % len(AGE_GROUPS)],
                        condition=condition,
                        visits=visits,
                        admissions=admissions,
                        avg_wait_minutes=wait,
                    )
                )
                counter += 1

    return records


def build_environmental_signals() -> list[EnvironmentalSignal]:
    values = {
        "Gasabo": [58, 62, 80, 86, 94, 116],
        "Kicukiro": [42, 39, 47, 51, 55, 61],
        "Nyarugenge": [35, 37, 41, 42, 46, 52],
    }

    signals: list[EnvironmentalSignal] = []
    for district, rainfall_values in values.items():
        for index, week in enumerate(WEEKS):
            signals.append(
                EnvironmentalSignal(
                    district=district,
                    week=week,
                    rainfall_mm=rainfall_values[index],
                    temperature_c=23.2 + index * 0.3,
                    air_quality_index=42 + index * 3,
                )
            )
    return signals
