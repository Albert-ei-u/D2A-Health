from app.services.alert_engine import generate_alerts
from app.services.analytics import average_wait, top_conditions, total_visits, weekly_volume
from app.services.ai_pipeline import run_ai_pipeline
from app.services.anomaly_detection import detect_condition_anomalies
from app.services.forecasting import forecast_total_volume
from app.services.synthetic_data import build_environmental_signals, build_patient_records


def test_dashboard_aggregations_are_populated() -> None:
    records = build_patient_records()

    assert total_visits(records) > 0
    assert average_wait(records) > 0
    assert len(top_conditions(records)) == 4
    assert len(weekly_volume(records)) == 6


def test_alert_engine_detects_malaria_spike() -> None:
    alerts = generate_alerts(build_patient_records())

    assert any(alert.condition == "Malaria" and alert.district == "Gasabo" for alert in alerts)


def test_anomaly_detection_scores_current_spike() -> None:
    anomalies = detect_condition_anomalies(build_patient_records())

    strongest = anomalies[0]
    assert strongest.district == "Gasabo"
    assert strongest.condition == "Malaria"
    assert strongest.score >= 0.65


def test_forecast_returns_next_week_volume_range() -> None:
    forecast = forecast_total_volume(build_patient_records())

    assert forecast.next_week == "2026-W25"
    assert forecast.lower_bound <= forecast.predicted_visits <= forecast.upper_bound
    assert forecast.trend_direction in {"rising", "stable", "falling"}


def test_ai_pipeline_returns_traceable_outputs() -> None:
    result = run_ai_pipeline(build_patient_records(), build_environmental_signals())

    assert result.alerts
    assert result.insights
    assert result.anomalies
    assert result.trace["pipeline"] == "ai-services-pipeline"
    assert len(result.trace["steps"]) >= 5
