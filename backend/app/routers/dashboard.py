from fastapi import APIRouter

from app.models import DashboardSummary
from app.services.alert_engine import generate_alerts
from app.services.analytics import (
    anomaly_summary,
    average_wait,
    current_environment,
    disease_trends,
    patient_volume_analysis,
    top_conditions,
    total_admissions,
    total_visits,
    weekly_volume,
)
from app.services.insight_engine import generate_insights
from app.services.synthetic_data import build_environmental_signals, build_patient_records

router = APIRouter()


@router.get("", response_model=DashboardSummary)
def get_dashboard() -> DashboardSummary:
    records = build_patient_records()
    environmental_signals = build_environmental_signals()
    alerts = generate_alerts(records, environmental_signals)

    return DashboardSummary(
        total_visits=total_visits(records),
        total_admissions=total_admissions(records),
        active_alerts=len(alerts),
        average_wait_minutes=average_wait(records),
        top_conditions=top_conditions(records),
        weekly_volume=weekly_volume(records),
        disease_trends=disease_trends(records),
        patient_volume_analysis=patient_volume_analysis(records),
        anomaly_signals=anomaly_summary(records),
        environmental_context=current_environment(environmental_signals),
        alerts=alerts,
        insights=generate_insights(records, environmental_signals),
    )
