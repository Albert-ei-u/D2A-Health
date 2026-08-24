from app.models import Alert, AlertSeverity, PatientRecord
from app.services.anomaly_detection import AnomalySignal, detect_condition_anomalies
from app.services.recommendation_engine import recommendations_for_anomaly
from app.services.tracing import ServiceTrace


def generate_alerts(records: list[PatientRecord]) -> list[Alert]:
    trace = ServiceTrace("alert-generation")
    trace.add("input", "Loaded anonymized patient records.", record_count=len(records))
    anomaly_signals = detect_condition_anomalies(records)
    trace.add(
        "anomaly-detection",
        "Compared latest week with historical baseline for each district and condition.",
        signal_count=len(anomaly_signals),
    )

    alerts: list[Alert] = []
    for signal in anomaly_signals:
        if not signal.is_significant:
            continue

        alerts.append(
            Alert(
                id=f"{signal.district.lower()}-{signal.condition.lower().replace(' ', '-')}",
                title=f"{signal.condition} increase in {signal.district}",
                severity=_severity_from_signal(signal),
                district=signal.district,
                condition=signal.condition,
                message=(
                    f"{signal.condition} visits in {signal.district} are "
                    f"{round(signal.percent_change * 100)}% above baseline."
                ),
                confidence=_confidence_from_signal(signal),
                evidence=[
                    f"Current week: {signal.current_week}.",
                    f"Current visits: {signal.current_visits}.",
                    f"Historical baseline: {signal.baseline_visits} visits.",
                    f"Anomaly z-score: {signal.z_score}.",
                    "Signal is based on anonymized facility-level visit counts.",
                    *recommendations_for_anomaly(signal)[:2],
                ],
            )
        )

    trace.add("alert-output", "Converted significant anomaly signals into alerts.", alert_count=len(alerts))
    return alerts


def _severity_from_signal(signal: AnomalySignal) -> AlertSeverity:
    if signal.score >= 0.85 or signal.percent_change >= 0.6:
        return AlertSeverity.high
    if signal.score >= 0.65:
        return AlertSeverity.medium
    return AlertSeverity.low


def _confidence_from_signal(signal: AnomalySignal) -> float:
    return min(0.92, round(0.55 + (signal.score * 0.4), 2))
