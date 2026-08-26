from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class UserRole(str, Enum):
    health_data_analyst = "Health Data Analyst"
    clinician = "Clinician"
    facility_manager = "Facility Manager"
    administrator = "Administrator"


class LoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


class UserProfile(BaseModel):
    email: str
    name: str
    role: UserRole


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
    name: str
    role: UserRole
    email: str


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
    latitude: float | None = None
    longitude: float | None = None


class FacilityLocation(BaseModel):
    facility: str
    district: str
    latitude: float
    longitude: float
    latest_week: str
    total_visits: int
    active_conditions: list[str]
    data_source: str


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
    active_data_source: str
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
    active_data_source: str
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
    active_data_source: str = "synthetic"
