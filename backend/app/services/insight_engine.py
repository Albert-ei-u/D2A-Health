from app.models import EnvironmentalSignal, Insight, PatientRecord
from app.services.analytics import top_conditions, weekly_volume


def generate_insights(
    records: list[PatientRecord], environmental_signals: list[EnvironmentalSignal]
) -> list[Insight]:
    ranked_conditions = top_conditions(records)
    volume = weekly_volume(records)
    latest_volume = volume[-1]["visits"]
    previous_volume = volume[-2]["visits"] if len(volume) > 1 else latest_volume
    growth = round(((latest_volume - previous_volume) / previous_volume) * 100) if previous_volume else 0

    highest_rainfall = max(environmental_signals, key=lambda signal: signal.rainfall_mm)

    return [
        Insight(
            id="volume-pressure",
            title="Patient volume pressure is rising",
            category="capacity",
            confidence=0.78,
            summary=f"Total visits increased by {growth}% in the latest reporting week.",
            considerations=[
                "Review triage coverage for peak clinic hours.",
                "Check whether pharmacy and laboratory queues are contributing to delays.",
                "Compare with upcoming staffing schedules before changing operations.",
            ],
            evidence=[
                f"Latest week volume: {latest_volume} visits.",
                f"Previous week volume: {previous_volume} visits.",
            ],
        ),
        Insight(
            id="condition-priority",
            title=f"{ranked_conditions[0]['condition']} is the leading reported condition",
            category="disease trend",
            confidence=0.81,
            summary="The top condition contributes the largest share of recent facility visits.",
            considerations=[
                "Review stock levels for related diagnostics and treatment.",
                "Confirm whether community health workers are reporting similar patterns.",
                "Prioritize field validation before public messaging.",
            ],
            evidence=[
                f"{ranked_conditions[0]['condition']}: {ranked_conditions[0]['visits']} visits.",
                f"{ranked_conditions[1]['condition']}: {ranked_conditions[1]['visits']} visits.",
            ],
        ),
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
        ),
    ]
