from fastapi import APIRouter

from app.models import DashboardSummary
from app.services.alert_engine import generate_alerts
from app.services.analytics import (
    average_wait,
    current_environment,
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
    alerts = generate_alerts(records)

    return DashboardSummary(
        total_visits=total_visits(records),
        total_admissions=total_admissions(records),
        active_alerts=len(alerts),
        average_wait_minutes=average_wait(records),
        top_conditions=top_conditions(records),
        weekly_volume=weekly_volume(records),
        environmental_context=current_environment(environmental_signals),
        alerts=alerts,
        insights=generate_insights(records, environmental_signals),
    )
