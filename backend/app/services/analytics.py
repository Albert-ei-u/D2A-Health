from collections import defaultdict

from app.models import EnvironmentalSignal, FacilityLocation, PatientRecord
from app.services.anomaly_detection import detect_condition_anomalies


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


def top_conditions(records: list[PatientRecord]) -> list[dict[str, int | str]]:
    totals: dict[str, int] = defaultdict(int)
    for record in records:
        totals[record.condition] += record.visits
    return [
        {"condition": condition, "visits": visits}
        for condition, visits in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]


def weekly_volume(records: list[PatientRecord]) -> list[dict[str, int | str]]:
    totals: dict[str, int] = defaultdict(int)
    for record in records:
        totals[record.week] += record.visits
    return [{"week": week, "visits": totals[week]} for week in sorted(totals)]


def disease_trends(records: list[PatientRecord]) -> list[dict[str, int | float | str]]:
    trends: list[dict[str, int | float | str]] = []
    groups = sorted({(record.district, record.condition) for record in records})

    for district, condition in groups:
        history = [
            record
            for record in sorted(records, key=lambda item: item.week)
            if record.district == district and record.condition == condition
        ]
        weekly_totals: dict[str, int] = defaultdict(int)
        for record in history:
            weekly_totals[record.week] += record.visits

        values = list(weekly_totals.values())
        if not values:
            continue

        first = values[0]
        previous = values[-2] if len(values) > 1 else values[-1]
        latest = values[-1]
        total = sum(values)
        week_over_week = _percent_change(previous, latest)
        overall_change = _percent_change(first, latest)

        trends.append(
            {
                "district": district,
                "condition": condition,
                "total_visits": total,
                "latest_week_visits": latest,
                "week_over_week_change_percent": week_over_week,
                "overall_change_percent": overall_change,
                "trend": _trend_label(overall_change),
            }
        )

    return sorted(
        trends,
        key=lambda item: (item["week_over_week_change_percent"], item["latest_week_visits"]),
        reverse=True,
    )


def patient_volume_analysis(records: list[PatientRecord]) -> list[dict[str, int | float | str]]:
    district_weeks: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    district_admissions: dict[str, int] = defaultdict(int)
    district_wait_weighted: dict[str, int] = defaultdict(int)

    for record in records:
        district_weeks[record.district][record.week] += record.visits
        district_admissions[record.district] += record.admissions
        district_wait_weighted[record.district] += record.avg_wait_minutes * record.visits

    analysis: list[dict[str, int | float | str]] = []
    for district, weeks in sorted(district_weeks.items()):
        ordered_weeks = [weeks[week] for week in sorted(weeks)]
        total = sum(ordered_weeks)
        latest = ordered_weeks[-1]
        previous = ordered_weeks[-2] if len(ordered_weeks) > 1 else latest
        avg_weekly = round(total / len(ordered_weeks), 1)
        wait = round(district_wait_weighted[district] / total) if total else 0
        admissions = district_admissions[district]

        analysis.append(
            {
                "district": district,
                "total_visits": total,
                "latest_week_visits": latest,
                "average_weekly_visits": avg_weekly,
                "week_over_week_change_percent": _percent_change(previous, latest),
                "admissions": admissions,
                "admission_rate_percent": round((admissions / total) * 100, 1) if total else 0,
                "average_wait_minutes": wait,
                "pressure_level": _pressure_level(latest, avg_weekly, wait),
            }
        )

    return sorted(analysis, key=lambda item: item["latest_week_visits"], reverse=True)


def anomaly_summary(records: list[PatientRecord]) -> list[dict[str, int | float | str | bool]]:
    return [
        {
            "district": signal.district,
            "condition": signal.condition,
            "week": signal.current_week,
            "current_visits": signal.current_visits,
            "baseline_visits": signal.baseline_visits,
            "absolute_change": signal.absolute_change,
            "percent_change": signal.percent_change,
            "z_score": signal.z_score,
            "score": signal.score,
            "is_significant": signal.is_significant,
        }
        for signal in detect_condition_anomalies(records, include_watchlist=True)
    ]


def facility_locations(records: list[PatientRecord], data_source: str) -> list[FacilityLocation]:
    grouped: dict[str, list[PatientRecord]] = defaultdict(list)
    for record in records:
        if record.latitude is None or record.longitude is None:
            continue
        grouped[f"{record.district}|{record.facility}"].append(record)

    locations: list[FacilityLocation] = []
    for facility_records in grouped.values():
        latest_week = max(record.week for record in facility_records)
        latest_records = [record for record in facility_records if record.week == latest_week]
        first = latest_records[0]

        locations.append(
            FacilityLocation(
                facility=first.facility,
                district=first.district,
                latitude=first.latitude or 0,
                longitude=first.longitude or 0,
                latest_week=latest_week,
                total_visits=sum(record.visits for record in latest_records),
                active_conditions=sorted({record.condition for record in latest_records}),
                data_source=data_source,
            )
        )

    return sorted(locations, key=lambda location: location.total_visits, reverse=True)


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


def _percent_change(previous: int | float, current: int | float) -> float:
    if previous == 0:
        return 0
    return round(((current - previous) / previous) * 100, 1)


def _trend_label(change_percent: float) -> str:
    if change_percent >= 20:
        return "rising"
    if change_percent <= -20:
        return "falling"
    return "stable"


def _pressure_level(latest: int, average: float, wait_minutes: int) -> str:
    if latest >= average * 1.25 or wait_minutes >= 45:
        return "high"
    if latest >= average * 1.1 or wait_minutes >= 36:
        return "medium"
    return "low"
