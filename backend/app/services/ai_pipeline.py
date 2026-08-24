from dataclasses import dataclass
from typing import Any

from app.models import Alert, EnvironmentalSignal, Insight, PatientRecord
from app.services.alert_engine import generate_alerts
from app.services.anomaly_detection import AnomalySignal, detect_condition_anomalies
from app.services.forecasting import VolumeForecast, forecast_total_volume
from app.services.insight_engine import generate_insights
from app.services.tracing import ServiceTrace


@dataclass(frozen=True)
class AIPipelineResult:
    alerts: list[Alert]
    insights: list[Insight]
    anomalies: list[AnomalySignal]
    forecast: VolumeForecast
    trace: dict[str, Any]


def run_ai_pipeline(
    records: list[PatientRecord],
    environmental_signals: list[EnvironmentalSignal],
) -> AIPipelineResult:
    trace = ServiceTrace("ai-services-pipeline")
    trace.add("input", "Received anonymized health records.", record_count=len(records))
    trace.add(
        "context",
        "Received environmental signals for contextual decision support.",
        signal_count=len(environmental_signals),
    )

    anomalies = detect_condition_anomalies(records)
    trace.add(
        "anomaly-detection",
        "Scored latest district-condition values against historical baselines.",
        anomaly_count=len(anomalies),
        strongest_score=anomalies[0].score if anomalies else 0,
    )

    forecast = forecast_total_volume(records)
    trace.add(
        "forecasting",
        "Projected next-week patient volume using a simple trend model.",
        predicted_visits=forecast.predicted_visits,
        trend_direction=forecast.trend_direction,
    )

    alerts = generate_alerts(records)
    trace.add("alert-generation", "Converted significant anomalies into warning alerts.", alert_count=len(alerts))

    insights = generate_insights(records, environmental_signals)
    trace.add(
        "insight-generation",
        "Generated decision-support insights with evidence and suggested considerations.",
        insight_count=len(insights),
    )

    return AIPipelineResult(
        alerts=alerts,
        insights=insights,
        anomalies=anomalies,
        forecast=forecast,
        trace=trace.as_dict(),
    )
