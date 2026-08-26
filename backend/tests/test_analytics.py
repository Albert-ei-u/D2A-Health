from fastapi.testclient import TestClient

from app.main import app
from app.services.alert_engine import generate_alerts
from app.services.analytics import (
    anomaly_summary,
    average_wait,
    disease_trends,
    facility_locations,
    patient_volume_analysis,
    top_conditions,
    total_visits,
    weekly_volume,
)
from app.services.ai_pipeline import run_ai_pipeline
from app.services.anomaly_detection import detect_condition_anomalies
from app.services.data_ingestion import parse_patient_csv
from app.services.forecasting import forecast_total_volume
from app.services.gemini_client import GeminiInsightResult
from app.services import insight_engine
from app.services.dataset_store import clear_uploaded_patient_records
from app.services.synthetic_data import build_environmental_signals, build_patient_records


def test_dashboard_aggregations_are_populated() -> None:
    records = build_patient_records()

    assert total_visits(records) > 0
    assert average_wait(records) > 0
    assert len(top_conditions(records)) == 4
    assert len(weekly_volume(records)) == 6
    assert disease_trends(records)
    assert patient_volume_analysis(records)
    assert anomaly_summary(records)
    assert facility_locations(records, "synthetic")


def test_alert_engine_detects_malaria_spike() -> None:
    alerts = generate_alerts(build_patient_records(), build_environmental_signals())

    malaria_alert = next(
        alert for alert in alerts if alert.condition == "Malaria" and alert.district == "Gasabo"
    )
    assert malaria_alert.confidence >= 0.65
    assert any("rainfall" in item for item in malaria_alert.evidence)
    assert any("baseline" in item for item in malaria_alert.evidence)


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


def test_dashboard_endpoint_returns_mvp_analysis_sections() -> None:
    clear_uploaded_patient_records()
    response = TestClient(app).get("/api/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["disease_trends"]
    assert payload["patient_volume_analysis"]
    assert payload["anomaly_signals"]
    assert payload["alerts"]
    assert payload["insights"]


def test_insight_engine_can_include_mocked_gemini_recommendation(monkeypatch) -> None:
    def fake_gemini(context: dict[str, object]) -> GeminiInsightResult:
        priority_locations = context["priority_locations"]
        assert priority_locations
        assert priority_locations[0]["latitude"]
        assert priority_locations[0]["longitude"]
        return GeminiInsightResult(
            title="Gemini recommends targeted malaria readiness",
            summary="Focus readiness on the district and condition with the strongest signal.",
            recommendations=["Validate the alert.", "Check supplies.", "Review staffing."],
            confidence=0.82,
            model="gemini-test",
        )

    monkeypatch.setattr(insight_engine, "generate_gemini_health_insight", fake_gemini)

    insights = insight_engine.generate_insights(
        build_patient_records(),
        build_environmental_signals(),
    )

    assert insights[0].id == "gemini-ai-recommendation"
    assert insights[0].confidence == 0.82
    assert any("Gemini model" in item for item in insights[0].evidence)


def test_csv_upload_becomes_active_dataset_for_dashboard() -> None:
    clear_uploaded_patient_records()
    csv_content = (
        "record_id,facility,district,week,age_group,condition,visits,admissions,avg_wait_minutes\n"
        "csv-001,Demo Clinic,Demo,2026-W21,18-59,Malaria,10,1,20\n"
        "csv-002,Demo Clinic,Demo,2026-W22,18-59,Malaria,12,1,22\n"
        "csv-003,Demo Clinic,Demo,2026-W23,18-59,Malaria,13,1,24\n"
        "csv-004,Demo Clinic,Demo,2026-W24,18-59,Malaria,40,3,45\n"
    )

    client = TestClient(app)
    upload_response = client.post(
        "/api/ingestion/patient-csv",
        files={"file": ("records.csv", csv_content, "text/csv")},
    )
    dashboard_response = client.get("/api/dashboard")
    clear_response = client.delete("/api/ingestion/patient-csv")

    assert upload_response.status_code == 200
    assert upload_response.json()["accepted_records"] == 4
    assert dashboard_response.status_code == 200
    payload = dashboard_response.json()
    assert payload["active_data_source"] == "csv_upload"
    assert payload["total_visits"] == 75
    assert payload["alerts"]
    assert payload["insights"]
    assert clear_response.json()["active_data_source"] == "synthetic"


def test_csv_upload_can_supply_exact_map_locations() -> None:
    clear_uploaded_patient_records()
    csv_content = (
        "record_id,facility,district,week,age_group,condition,visits,admissions,"
        "avg_wait_minutes,latitude,longitude\n"
        "csv-001,Demo Clinic,Demo,2026-W21,18-59,Malaria,10,1,20,-1.9500,30.0600\n"
        "csv-002,Demo Clinic,Demo,2026-W22,18-59,Malaria,12,1,22,-1.9500,30.0600\n"
        "csv-003,Demo Clinic,Demo,2026-W23,18-59,Malaria,13,1,24,-1.9500,30.0600\n"
        "csv-004,Demo Clinic,Demo,2026-W24,18-59,Malaria,40,3,45,-1.9500,30.0600\n"
    )

    client = TestClient(app)
    client.post(
        "/api/ingestion/patient-csv",
        files={"file": ("records.csv", csv_content, "text/csv")},
    )
    response = client.get("/api/records/locations")
    clear_uploaded_patient_records()

    assert response.status_code == 200
    locations = response.json()
    assert locations[0]["facility"] == "Demo Clinic"
    assert locations[0]["data_source"] == "csv_upload"
    assert locations[0]["latitude"] == -1.95
    assert locations[0]["longitude"] == 30.06
    assert locations[0]["total_visits"] == 40


def test_csv_ingestion_rejects_duplicate_ids_and_invalid_admissions() -> None:
    csv_content = (
        "record_id,facility,district,week,age_group,condition,visits,admissions,avg_wait_minutes\n"
        "row-001,Demo Clinic,Demo,2026-W23,18-59,Malaria,10,2,20\n"
        "row-002,Demo Clinic,Demo,2026-W24,18-59,Malaria,8,9,20\n"
        "row-001,Demo Clinic,Demo,2026-W24,18-59,Malaria,8,1,20\n"
    )

    result = parse_patient_csv(csv_content)

    assert result.accepted_records == 1
    assert result.rejected_records == 2
    assert any("admissions cannot exceed visits" in error for error in result.errors)
    assert any("duplicate record_id" in error for error in result.errors)
