from dataclasses import dataclass

from app.models import PatientRecord


@dataclass(frozen=True)
class VolumeForecast:
    next_week: str
    predicted_visits: int
    lower_bound: int
    upper_bound: int
    trend_direction: str
    confidence: float


def forecast_total_volume(records: list[PatientRecord]) -> VolumeForecast:
    weekly_totals = _weekly_totals(records)
    if len(weekly_totals) < 2:
        return VolumeForecast(
            next_week="next",
            predicted_visits=0,
            lower_bound=0,
            upper_bound=0,
            trend_direction="stable",
            confidence=0.35,
        )

    points = list(enumerate(weekly_totals.values(), start=1))
    slope = _linear_regression_slope(points)
    latest_week = next(reversed(weekly_totals))
    latest_value = weekly_totals[latest_week]
    predicted = max(0, round(latest_value + slope))
    margin = max(8, round(predicted * 0.08))
    direction = "rising" if slope > 4 else "falling" if slope < -4 else "stable"

    return VolumeForecast(
        next_week=_increment_week(latest_week),
        predicted_visits=predicted,
        lower_bound=max(0, predicted - margin),
        upper_bound=predicted + margin,
        trend_direction=direction,
        confidence=0.7 if direction != "stable" else 0.62,
    )


def _weekly_totals(records: list[PatientRecord]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for record in sorted(records, key=lambda item: item.week):
        totals[record.week] = totals.get(record.week, 0) + record.visits
    return totals


def _linear_regression_slope(points: list[tuple[int, int]]) -> float:
    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]
    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in points)
    denominator = sum((x - x_mean) ** 2 for x in x_values)
    return numerator / denominator if denominator else 0


def _increment_week(week: str) -> str:
    year, week_number = week.split("-W")
    return f"{year}-W{int(week_number) + 1:02d}"
