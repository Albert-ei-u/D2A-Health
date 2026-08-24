from dataclasses import dataclass, field
from time import perf_counter
from typing import Any


@dataclass
class TraceStep:
    name: str
    detail: str
    data: dict[str, Any] = field(default_factory=dict)
    elapsed_ms: float = 0


@dataclass
class ServiceTrace:
    pipeline: str
    steps: list[TraceStep] = field(default_factory=list)
    _last_checkpoint: float = field(default_factory=perf_counter)

    def add(self, name: str, detail: str, **data: Any) -> None:
        now = perf_counter()
        self.steps.append(
            TraceStep(
                name=name,
                detail=detail,
                data=data,
                elapsed_ms=round((now - self._last_checkpoint) * 1000, 2),
            )
        )
        self._last_checkpoint = now

    def as_evidence(self) -> list[str]:
        return [
            f"{step.name}: {step.detail}"
            for step in self.steps
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "pipeline": self.pipeline,
            "steps": [
                {
                    "name": step.name,
                    "detail": step.detail,
                    "data": step.data,
                    "elapsed_ms": step.elapsed_ms,
                }
                for step in self.steps
            ],
        }
