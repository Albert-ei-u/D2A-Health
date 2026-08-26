from app.models import Alert, AlertSeverity, EnvironmentalSignal, PatientRecord
from app.services.anomaly_detection import AnomalySignal, detect_condition_anomalies
from app.services.recommendation_engine import recommendations_for_anomaly
from app.services.tracing import ServiceTrace


def generate_alerts(
    records: list[PatientRecord],
    environmental_signals: list[EnvironmentalSignal] | None = None,
) -> list[Alert]:
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
                message=_alert_message(signal),
                confidence=_confidence_from_signal(signal),
                evidence=_alert_evidence(signal, environmental_signals),
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
    return min(0.94, round(0.54 + (signal.score * 0.42), 2))


def _alert_message(signal: AnomalySignal) -> str:
    return (
        f"{signal.condition} visits in {signal.district} are "
        f"{round(signal.percent_change * 100)}% above baseline for {signal.current_week}."
    )


def _alert_evidence(
    signal: AnomalySignal,
    environmental_signals: list[EnvironmentalSignal] | None,
) -> list[str]:
    evidence = [
        signal.explanation,
        f"Current week: {signal.current_week}.",
        f"Current visits: {signal.current_visits}.",
        f"Historical baseline: {signal.baseline_visits} visits.",
        f"Absolute change: {signal.absolute_change} visits.",
        f"Anomaly score: {signal.score}.",
        "Data source: anonymized facility-level synthetic records.",
    ]

    context = _environment_for_signal(signal, environmental_signals or [])
    if context:
        evidence.append(context)

    evidence.extend(recommendations_for_anomaly(signal)[:2])
    return evidence


def _environment_for_signal(
    signal: AnomalySignal,
    environmental_signals: list[EnvironmentalSignal],
) -> str | None:
    matching = [
        item
        for item in environmental_signals
        if item.district == signal.district and item.week == signal.current_week
    ]
    if not matching:
        return None

    context = matching[0]
    return (
        "Context: "
        f"rainfall {context.rainfall_mm} mm, temperature {context.temperature_c} C, "
        f"air quality index {context.air_quality_index}."
    )
