from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PatientRecordRow(Base):
    __tablename__ = "patient_records"

    record_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    facility: Mapped[str] = mapped_column(String(200), nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False)
    village: Mapped[str | None] = mapped_column(String(120), nullable=True)
    week: Mapped[str] = mapped_column(String(20), nullable=False)
    age_group: Mapped[str] = mapped_column(String(50), nullable=False)
    condition: Mapped[str] = mapped_column(String(120), nullable=False)
    visits: Mapped[int] = mapped_column(Integer, nullable=False)
    admissions: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_wait_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

class UserPatientRecordRow(Base):
    __tablename__ = "user_patient_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_email: Mapped[str] = mapped_column(String(320), index=True, nullable=False)
    record_id: Mapped[str] = mapped_column(String(120), nullable=False)
    facility: Mapped[str] = mapped_column(String(200), nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False)
    village: Mapped[str | None] = mapped_column(String(120), nullable=True)
    week: Mapped[str] = mapped_column(String(20), nullable=False)
    age_group: Mapped[str] = mapped_column(String(50), nullable=False)
    condition: Mapped[str] = mapped_column(String(120), nullable=False)
    visits: Mapped[int] = mapped_column(Integer, nullable=False)
    admissions: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_wait_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)


class UserRow(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(300), nullable=False)
    role: Mapped[str] = mapped_column(String(80), nullable=False)
    health_center: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    dataset_ready: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class VerificationCodeRow(Base):
    __tablename__ = "verification_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), index=True, nullable=False)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
