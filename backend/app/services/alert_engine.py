from app.models import Alert, AlertSeverity, PatientRecord
from app.services.analytics import condition_growth


def generate_alerts(records: list[PatientRecord]) -> list[Alert]:
    alerts: list[Alert] = []
    pairs = sorted({(record.district, record.condition) for record in records})

    for district, condition in pairs:
        growth = condition_growth(records, district, condition)
        if growth < 0.25:
            continue

        severity = AlertSeverity.high if growth >= 0.5 else AlertSeverity.medium
        confidence = 0.86 if severity == AlertSeverity.high else 0.72

        alerts.append(
            Alert(
                id=f"{district.lower()}-{condition.lower().replace(' ', '-')}",
                title=f"{condition} increase in {district}",
                severity=severity,
                district=district,
                condition=condition,
                message=(
                    f"{condition} visits in {district} rose by {round(growth * 100)}% "
                    "compared with the previous reporting week."
                ),
                confidence=confidence,
                evidence=[
                    "Current week is above the recent historical pattern.",
                    "Signal is based on anonymized facility-level visit counts.",
                    "Review staffing, supplies, and local context before action.",
                ],
            )
        )

    return alerts
