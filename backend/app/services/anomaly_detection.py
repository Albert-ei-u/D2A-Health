from dataclasses import dataclass
from statistics import mean, pstdev

from app.models import PatientRecord


@dataclass(frozen=True)
class AnomalySignal:
    district: str
    condition: str
    current_week: str
    current_visits: int
    baseline_visits: float
    absolute_change: float
    percent_change: float
    z_score: float
    score: float
    explanation: str

    @property
    def is_significant(self) -> bool:
        return self.score >= 0.65


def detect_condition_anomalies(
    records: list[PatientRecord],
    min_percent_change: float = 0.25,
    include_watchlist: bool = False,
) -> list[AnomalySignal]:
    signals: list[AnomalySignal] = []
    pairs = sorted({(record.district, record.condition) for record in records})

    for district, condition in pairs:
        history = sorted(
            [
                record
                for record in records
                if record.district == district and record.condition == condition
            ],
            key=lambda record: record.week,
        )
        if len(history) < 3:
            continue

        previous_records = history[:-1]
        current = history[-1]
        baseline = mean(record.visits for record in previous_records)
        spread = pstdev(record.visits for record in previous_records) or 1
        absolute_change = current.visits - baseline
        percent_change = absolute_change / baseline if baseline else 0
        z_score = absolute_change / spread

        is_watchlist_signal = percent_change >= min_percent_change or z_score >= 2
        if not include_watchlist and not is_watchlist_signal:
            continue

        score = _score_anomaly(percent_change, z_score)
        if include_watchlist and score < 0.35:
            continue

        signals.append(
            AnomalySignal(
                district=district,
                condition=condition,
                current_week=current.week,
                current_visits=current.visits,
                baseline_visits=round(baseline, 2),
                absolute_change=round(absolute_change, 2),
                percent_change=round(percent_change, 3),
                z_score=round(z_score, 2),
                score=score,
                explanation=_explain_anomaly(current.visits, baseline, percent_change, z_score),
            )
        )

    return sorted(signals, key=lambda signal: signal.score, reverse=True)


def _score_anomaly(percent_change: float, z_score: float) -> float:
    percent_component = min(max(percent_change / 0.75, 0), 1)
    z_component = min(max(z_score / 4, 0), 1)
    return round((percent_component * 0.55) + (z_component * 0.45), 2)


def _explain_anomaly(
    current_visits: int,
    baseline_visits: float,
    percent_change: float,
    z_score: float,
) -> str:
    percent = round(percent_change * 100)
    return (
        f"Latest visits ({current_visits}) are {percent}% above the historical "
        f"baseline ({round(baseline_visits, 1)}), with a z-score of {round(z_score, 2)}."
    )
