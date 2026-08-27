from fastapi import APIRouter, Header

from app.models import DashboardSummary
from app.services.alert_engine import generate_alerts
from app.services.forecasting import forecast_by_district
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
from app.services.dataset_store import active_data_source, require_user_dataset
from app.services.insight_engine import generate_insights

router = APIRouter()


@router.get("", response_model=DashboardSummary)
def get_dashboard(x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> DashboardSummary:
    records = require_user_dataset(x_user_email)
    environmental_signals = []
    alerts = generate_alerts(records, environmental_signals)
    district_forecasts = [
        {
            "district": district,
            "next_week": forecast.next_week,
            "current_visits": current,
            "predicted_visits": forecast.predicted_visits,
            "lower_bound": forecast.lower_bound,
            "upper_bound": forecast.upper_bound,
            "trend_direction": forecast.trend_direction,
            "confidence": forecast.confidence,
        }
        for district, forecast, current in forecast_by_district(records)
    ]

    return DashboardSummary(
        active_data_source=active_data_source(x_user_email),
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
        district_forecasts=district_forecasts,
    )
