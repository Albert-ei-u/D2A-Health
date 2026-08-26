from app.models import EnvironmentalSignal, PatientRecord

WEEKS = ["2026-W19", "2026-W20", "2026-W21", "2026-W22", "2026-W23", "2026-W24"]
DISTRICTS = ["Gasabo", "Kicukiro", "Nyarugenge"]
CONDITIONS = ["Malaria", "Respiratory infection", "Diarrheal disease", "Hypertension"]
AGE_GROUPS = ["0-5", "6-17", "18-59", "60+"]
FACILITIES_BY_DISTRICT = {
    "Gasabo": ["Kacyiru Health Centre", "Gasabo District Hospital"],
    "Kicukiro": ["Masaka Health Centre", "Kicukiro District Hospital"],
    "Nyarugenge": ["Muhima Health Centre", "Nyarugenge District Hospital"],
}
FACILITY_COORDINATES = {
    "Kacyiru Health Centre": (-1.9326, 30.0870),
    "Gasabo District Hospital": (-1.8847, 30.1127),
    "Masaka Health Centre": (-1.9977, 30.2172),
    "Kicukiro District Hospital": (-1.9738, 30.1044),
    "Muhima Health Centre": (-1.9441, 30.0579),
    "Nyarugenge District Hospital": (-1.9545, 30.0606),
}

CONDITION_PROFILES = {
    "Malaria": {"baseline": 24, "weekly_trend": 3, "admission_rate": 0.09, "wait_impact": 0.45},
    "Respiratory infection": {
        "baseline": 20,
        "weekly_trend": 2,
        "admission_rate": 0.07,
        "wait_impact": 0.38,
    },
    "Diarrheal disease": {"baseline": 15, "weekly_trend": 1, "admission_rate": 0.06, "wait_impact": 0.34},
    "Hypertension": {"baseline": 13, "weekly_trend": 1, "admission_rate": 0.12, "wait_impact": 0.28},
}

DISTRICT_LOAD_FACTORS = {
    "Gasabo": 1.18,
    "Kicukiro": 1.0,
    "Nyarugenge": 0.88,
}

FACILITY_LOAD_FACTORS = {
    "Health Centre": 0.46,
    "District Hospital": 0.68,
}


def build_patient_records() -> list[PatientRecord]:
    records: list[PatientRecord] = []
    counter = 1

    for week_index, week in enumerate(WEEKS):
        for district in DISTRICTS:
            for condition_index, condition in enumerate(CONDITIONS):
                profile = CONDITION_PROFILES[condition]
                for facility_index, facility in enumerate(FACILITIES_BY_DISTRICT[district]):
                    facility_factor_key = (
                        "District Hospital" if "District Hospital" in facility else "Health Centre"
                    )
                    seasonal_pressure = 1 + (week_index * profile["weekly_trend"] * 0.035)
                    local_variation = 1 + (((week_index + condition_index + facility_index) % 3) - 1) * 0.04
                    spike = _outbreak_spike(week, district, condition, facility)
                    visits = round(
                        profile["baseline"]
                        * DISTRICT_LOAD_FACTORS[district]
                        * FACILITY_LOAD_FACTORS[facility_factor_key]
                        * seasonal_pressure
                        * local_variation
                    ) + spike
                    admissions = max(1, round(visits * profile["admission_rate"]))
                    wait = round(22 + visits * profile["wait_impact"] + week_index * 1.7 + spike * 0.22)

                    records.append(
                        PatientRecord(
                            record_id=f"anon-{counter:04d}",
                            facility=facility,
                            district=district,
                            week=week,
                            age_group=AGE_GROUPS[
                                (week_index + condition_index + facility_index) % len(AGE_GROUPS)
                            ],
                            condition=condition,
                            visits=visits,
                            admissions=admissions,
                            avg_wait_minutes=wait,
                            latitude=FACILITY_COORDINATES[facility][0],
                            longitude=FACILITY_COORDINATES[facility][1],
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


def _outbreak_spike(week: str, district: str, condition: str, facility: str) -> int:
    if week == "2026-W24" and district == "Gasabo" and condition == "Malaria":
        return 34 if "District Hospital" in facility else 22
    if week == "2026-W23" and district == "Nyarugenge" and condition == "Respiratory infection":
        return 12 if "District Hospital" in facility else 7
    if week == "2026-W24" and district == "Kicukiro" and condition == "Diarrheal disease":
        return 10 if "District Hospital" in facility else 6
    return 0
