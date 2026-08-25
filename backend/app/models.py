from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class PatientRecord(BaseModel):
    record_id: str
    facility: str
    district: str
    week: str
    age_group: str
    condition: str
    visits: int = Field(ge=0)
    admissions: int = Field(ge=0)
    avg_wait_minutes: int = Field(ge=0)


class EnvironmentalSignal(BaseModel):
    district: str
    week: str
    rainfall_mm: float
    temperature_c: float
    air_quality_index: int


class Alert(BaseModel):
    id: str
    title: str
    severity: AlertSeverity
    district: str
    condition: str
    message: str
    confidence: float = Field(ge=0, le=1)
    evidence: list[str]


class Insight(BaseModel):
    id: str
    title: str
    category: str
    confidence: float = Field(ge=0, le=1)
    summary: str
    considerations: list[str]
    evidence: list[str]


class DashboardSummary(BaseModel):
    total_visits: int
    total_admissions: int
    active_alerts: int
    average_wait_minutes: int
    top_conditions: list[dict[str, Any]]
    weekly_volume: list[dict[str, Any]]
    disease_trends: list[dict[str, Any]]
    patient_volume_analysis: list[dict[str, Any]]
    anomaly_signals: list[dict[str, Any]]
    environmental_context: list[EnvironmentalSignal]
    alerts: list[Alert]
    insights: list[Insight]


class AIPipelineResponse(BaseModel):
    alerts: list[Alert]
    insights: list[Insight]
    anomalies: list[dict[str, Any]]
    forecast: dict[str, Any]
    trace: dict[str, Any]


class IngestionResult(BaseModel):
    accepted_records: int
    rejected_records: int
    records: list[PatientRecord]
    errors: list[str]
