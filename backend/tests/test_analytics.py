from app.services.alert_engine import generate_alerts
from app.services.analytics import average_wait, top_conditions, total_visits, weekly_volume
from app.services.synthetic_data import build_patient_records


def test_dashboard_aggregations_are_populated() -> None:
    records = build_patient_records()

    assert total_visits(records) > 0
    assert average_wait(records) > 0
    assert len(top_conditions(records)) == 4
    assert len(weekly_volume(records)) == 6


def test_alert_engine_detects_malaria_spike() -> None:
    alerts = generate_alerts(build_patient_records())

    assert any(alert.condition == "Malaria" and alert.district == "Gasabo" for alert in alerts)
