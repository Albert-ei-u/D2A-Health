from app.services.anomaly_detection import AnomalySignal
from app.services.forecasting import VolumeForecast


def recommendations_for_anomaly(signal: AnomalySignal) -> list[str]:
    recommendations = [
        "Validate the signal with facility staff before making operational changes.",
        "Compare the latest cases with stock levels, staffing, and triage capacity.",
    ]

    if signal.condition == "Malaria":
        recommendations.extend(
            [
                "Check availability of malaria rapid tests and first-line treatment.",
                "Review rainfall and vector-control context for the affected district.",
            ]
        )
    elif signal.condition == "Respiratory infection":
        recommendations.extend(
            [
                "Review respiratory triage flow and protective-equipment readiness.",
                "Check whether school or community clusters are being reported.",
            ]
        )
    elif signal.condition == "Diarrheal disease":
        recommendations.extend(
            [
                "Check oral rehydration supply and water/sanitation reports.",
                "Compare with community-level reports before escalation.",
            ]
        )
    else:
        recommendations.append("Review chronic-care appointment backlog and refill continuity.")

    return recommendations


def recommendations_for_forecast(forecast: VolumeForecast) -> list[str]:
    if forecast.trend_direction == "rising":
        return [
            "Prepare staffing coverage for a higher patient load next week.",
            "Prioritize departments linked to the highest current disease burden.",
            "Monitor whether wait times rise with the forecasted volume.",
        ]

    if forecast.trend_direction == "falling":
        return [
            "Keep monitoring to confirm the decline before reallocating resources.",
            "Use the lower demand window for backlog review and follow-ups.",
        ]

    return [
        "Maintain current staffing while watching for district-specific anomalies.",
        "Focus action on alerts rather than total-volume change.",
    ]
