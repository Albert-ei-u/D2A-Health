from collections import defaultdict

from app.models import EnvironmentalSignal, PatientRecord


def total_visits(records: list[PatientRecord]) -> int:
    return sum(record.visits for record in records)


def total_admissions(records: list[PatientRecord]) -> int:
    return sum(record.admissions for record in records)


def average_wait(records: list[PatientRecord]) -> int:
    if not records:
        return 0
    weighted_wait = sum(record.avg_wait_minutes * record.visits for record in records)
    visits = total_visits(records)
    return round(weighted_wait / visits) if visits else 0


def top_conditions(records: list[PatientRecord]) -> list[dict[str, int]]:
    totals: dict[str, int] = defaultdict(int)
    for record in records:
        totals[record.condition] += record.visits
    return [
        {"condition": condition, "visits": visits}
        for condition, visits in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]


def weekly_volume(records: list[PatientRecord]) -> list[dict[str, int]]:
    totals: dict[str, int] = defaultdict(int)
    for record in records:
        totals[record.week] += record.visits
    return [{"week": week, "visits": totals[week]} for week in sorted(totals)]


def current_environment(signals: list[EnvironmentalSignal]) -> list[EnvironmentalSignal]:
    if not signals:
        return []
    latest_week = max(signal.week for signal in signals)
    return [signal for signal in signals if signal.week == latest_week]


def condition_growth(records: list[PatientRecord], district: str, condition: str) -> float:
    matching = [
        record for record in records if record.district == district and record.condition == condition
    ]
    matching.sort(key=lambda record: record.week)
    if len(matching) < 2:
        return 0

    previous = matching[-2].visits
    current = matching[-1].visits
    if previous == 0:
        return 0
    return (current - previous) / previous


def condition_history(
    records: list[PatientRecord], district: str, condition: str
) -> list[dict[str, int]]:
    history = [
        {"week": record.week, "visits": record.visits}
        for record in records
        if record.district == district and record.condition == condition
    ]
    return sorted(history, key=lambda item: item["week"])


def district_wait_pressure(records: list[PatientRecord]) -> list[dict[str, int]]:
    district_visits: dict[str, int] = defaultdict(int)
    weighted_waits: dict[str, int] = defaultdict(int)

    for record in records:
        district_visits[record.district] += record.visits
        weighted_waits[record.district] += record.avg_wait_minutes * record.visits

    return [
        {
            "district": district,
            "average_wait_minutes": round(weighted_waits[district] / visits),
        }
        for district, visits in sorted(district_visits.items())
        if visits
    ]
