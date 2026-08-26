from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PatientRecordRow(Base):
    __tablename__ = "patient_records"

    record_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    facility: Mapped[str] = mapped_column(String(200), nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False)
    week: Mapped[str] = mapped_column(String(20), nullable=False)
    age_group: Mapped[str] = mapped_column(String(50), nullable=False)
    condition: Mapped[str] = mapped_column(String(120), nullable=False)
    visits: Mapped[int] = mapped_column(Integer, nullable=False)
    admissions: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_wait_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
