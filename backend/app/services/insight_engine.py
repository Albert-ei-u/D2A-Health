from app.models import EnvironmentalSignal, Insight, PatientRecord
from app.services.analytics import (
    disease_trends,
    district_wait_pressure,
    patient_volume_analysis,
    top_conditions,
    weekly_volume,
)
from app.services.anomaly_detection import detect_condition_anomalies
from app.services.forecasting import forecast_total_volume
from app.services.gemini_client import generate_gemini_health_insight
from app.services.recommendation_engine import (
    recommendations_for_anomaly,
    recommendations_for_forecast,
)
from app.services.tracing import ServiceTrace


def generate_insights(
    records: list[PatientRecord], environmental_signals: list[EnvironmentalSignal]
) -> list[Insight]:
    trace = ServiceTrace("insight-generation")
    trace.add("input", "Loaded records and environmental context.", record_count=len(records))

    if not records:
        return [
            Insight(
                id="insufficient-data",
                title="Insufficient data for AI insight generation",
                category="data quality",
                confidence=0.4,
                summary="No patient records were available for analysis.",
                considerations=[
                    "Confirm that the data ingestion pipeline is running.",
                    "Check whether records were filtered out during validation.",
                ],
                evidence=trace.as_evidence(),
            )
        ]

    ranked_conditions = top_conditions(records)
    top_condition = ranked_conditions[0]
    comparison_condition = ranked_conditions[1] if len(ranked_conditions) > 1 else None
    trends = disease_trends(records)
    fastest_rising = trends[0] if trends else None
    volume_pressure = patient_volume_analysis(records)
    highest_pressure = volume_pressure[0] if volume_pressure else None
    volume = weekly_volume(records)
    latest_volume = volume[-1]["visits"]
    previous_volume = volume[-2]["visits"] if len(volume) > 1 else latest_volume
    growth = round(((latest_volume - previous_volume) / previous_volume) * 100) if previous_volume else 0
    highest_rainfall = (
        max(environmental_signals, key=lambda signal: signal.rainfall_mm)
        if environmental_signals
        else None
    )
    forecast = forecast_total_volume(records)
    anomalies = detect_condition_anomalies(records)
    strongest_anomaly = anomalies[0] if anomalies else None
    wait_pressure = max(district_wait_pressure(records), key=lambda item: item["average_wait_minutes"])

    trace.add(
        "feature-extraction",
        "Calculated volume growth, leading conditions, wait pressure, rainfall context, and anomalies.",
        growth_percent=growth,
        anomaly_count=len(anomalies),
    )

    insights = [
        Insight(
            id="volume-pressure",
            title=f"Patient volume is {forecast.trend_direction}",
            category="capacity",
            confidence=forecast.confidence,
            summary=(
                f"Total visits changed by {growth}% in the latest week. "
                f"Next week forecast is {forecast.predicted_visits} visits "
                f"({forecast.lower_bound}-{forecast.upper_bound})."
            ),
            considerations=recommendations_for_forecast(forecast),
            evidence=[
                f"Latest week volume: {latest_volume} visits.",
                f"Previous week volume: {previous_volume} visits.",
                f"Forecast week: {forecast.next_week}.",
            ],
        ),
        Insight(
            id="condition-priority",
            title=f"{top_condition['condition']} is the leading reported condition",
            category="disease trend",
            confidence=0.83,
            summary=(
                "The top condition contributes the largest share of facility visits in the "
                "synthetic MVP dataset."
            ),
            considerations=[
                "Review stock levels for related diagnostics and treatment.",
                "Confirm whether community health workers are reporting similar patterns.",
                "Prioritize field validation before public messaging.",
            ],
            evidence=[
                f"{top_condition['condition']}: {top_condition['visits']} visits.",
                *(
                    [f"{comparison_condition['condition']}: {comparison_condition['visits']} visits."]
                    if comparison_condition
                    else []
                ),
            ],
        ),
        Insight(
            id="wait-pressure",
            title=f"{wait_pressure['district']} has the highest wait pressure",
            category="operations",
            confidence=0.73,
            summary=(
                f"{wait_pressure['district']} has an average wait of "
                f"{wait_pressure['average_wait_minutes']} minutes across the synthetic records."
            ),
            considerations=[
                "Compare patient arrival times with staffing coverage.",
                "Check whether laboratory, pharmacy, or triage queues explain the delay.",
                "Prioritize workflow review before increasing alerts to staff.",
            ],
            evidence=[
                f"District: {wait_pressure['district']}.",
                f"Average wait: {wait_pressure['average_wait_minutes']} minutes.",
            ],
        ),
    ]

    if fastest_rising:
        insights.insert(
            1,
            Insight(
                id="fastest-rising-condition",
                title=(
                    f"{fastest_rising['condition']} is rising fastest in "
                    f"{fastest_rising['district']}"
                ),
                category="disease trend",
                confidence=0.78,
                summary=(
                    f"Latest week visits changed by "
                    f"{fastest_rising['week_over_week_change_percent']}% compared with the prior week."
                ),
                considerations=[
                    "Check whether the increase is concentrated in one facility or age group.",
                    "Compare with community surveillance before confirming an outbreak.",
                    "Prepare targeted follow-up if the trend continues next week.",
                ],
                evidence=[
                    f"District: {fastest_rising['district']}.",
                    f"Condition: {fastest_rising['condition']}.",
                    f"Latest week visits: {fastest_rising['latest_week_visits']}.",
                    f"Overall trend: {fastest_rising['trend']}.",
                ],
            ),
        )

    if highest_pressure:
        insights.append(
            Insight(
                id="patient-volume-pressure",
                title=f"{highest_pressure['district']} has the highest latest patient volume",
                category="capacity",
                confidence=0.76,
                summary=(
                    f"{highest_pressure['district']} reported "
                    f"{highest_pressure['latest_week_visits']} latest-week visits and "
                    f"{highest_pressure['pressure_level']} operational pressure."
                ),
                considerations=[
                    "Review staffing coverage against the latest patient load.",
                    "Check whether high-volume departments overlap with active alerts.",
                    "Use this signal for planning, not individual patient decision-making.",
                ],
                evidence=[
                    f"Average weekly visits: {highest_pressure['average_weekly_visits']}.",
                    f"Average wait: {highest_pressure['average_wait_minutes']} minutes.",
                    f"Admission rate: {highest_pressure['admission_rate_percent']}%.",
                ],
            )
        )

    if strongest_anomaly:
        insights.insert(
            0,
            Insight(
                id="strongest-anomaly",
                title=f"Strongest signal: {strongest_anomaly.condition} in {strongest_anomaly.district}",
                category="early warning",
                confidence=min(0.93, round(0.56 + strongest_anomaly.score * 0.4, 2)),
                summary=(
                    f"Latest visits are {round(strongest_anomaly.percent_change * 100)}% "
                    "above the historical baseline for this district and condition."
                ),
                considerations=recommendations_for_anomaly(strongest_anomaly),
                evidence=[
                    f"Current visits: {strongest_anomaly.current_visits}.",
                    f"Baseline visits: {strongest_anomaly.baseline_visits}.",
                    f"Z-score: {strongest_anomaly.z_score}.",
                ],
            ),
        )

    if highest_rainfall:
        insights.append(
            Insight(
                id="environment-context",
                title="Environmental context may affect demand",
                category="context",
                confidence=0.67,
                summary=(
                    f"{highest_rainfall.district} shows the highest rainfall signal "
                    f"at {highest_rainfall.rainfall_mm} mm."
                ),
                considerations=[
                    "Use this as context, not proof of causation.",
                    "Compare with confirmed local surveillance and weather reports.",
                    "Watch waterborne and vector-borne conditions in follow-up data.",
                ],
                evidence=[
                    f"District: {highest_rainfall.district}.",
                    f"Reporting week: {highest_rainfall.week}.",
                ],
            )
        )

    gemini_result = generate_gemini_health_insight(
        {
            "latest_total_visits": latest_volume,
            "previous_total_visits": previous_volume,
            "growth_percent": growth,
            "top_conditions": ranked_conditions[:3],
            "fastest_rising_trend": fastest_rising,
            "highest_volume_pressure": highest_pressure,
            "strongest_anomaly": (
                {
                    "district": strongest_anomaly.district,
                    "condition": strongest_anomaly.condition,
                    "current_week": strongest_anomaly.current_week,
                    "current_visits": strongest_anomaly.current_visits,
                    "baseline_visits": strongest_anomaly.baseline_visits,
                    "percent_change": strongest_anomaly.percent_change,
                    "score": strongest_anomaly.score,
                }
                if strongest_anomaly
                else None
            ),
            "highest_rainfall": (
                {
                    "district": highest_rainfall.district,
                    "week": highest_rainfall.week,
                    "rainfall_mm": highest_rainfall.rainfall_mm,
                    "temperature_c": highest_rainfall.temperature_c,
                    "air_quality_index": highest_rainfall.air_quality_index,
                }
                if highest_rainfall
                else None
            ),
        }
    )
    if gemini_result:
        insights.insert(
            0,
            Insight(
                id="gemini-ai-recommendation",
                title=gemini_result.title,
                category="ai recommendation",
                confidence=gemini_result.confidence,
                summary=gemini_result.summary,
                considerations=gemini_result.recommendations,
                evidence=[
                    f"Generated by Gemini model: {gemini_result.model}.",
                    "Prompt used anonymized aggregate MVP metrics only.",
                    "Rule-based analytics remain available as fallback evidence.",
                    *(
                        [f"Raw Gemini preview: {gemini_result.raw_preview}"]
                        if gemini_result.raw_preview
                        and gemini_result.summary == "Gemini responded, but the response was not valid JSON."
                        else []
                    ),
                ],
            ),
        )
        trace.add(
            "gemini-generation",
            "Generated an external AI recommendation using Gemini.",
            model=gemini_result.model,
        )

    trace.add("insight-output", "Generated decision-support insights.", insight_count=len(insights))
    return insights
