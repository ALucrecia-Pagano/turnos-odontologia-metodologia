from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProfessionalModel(Base):
    __tablename__ = "professional"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    license_number: Mapped[str | None] = mapped_column(String(50), nullable=True)


class ChairModel(Base):
    __tablename__ = "chair"
    __table_args__ = (
        Index("ux_chair_name_normalized", "name_normalized", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_normalized: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ServiceModel(Base):
    __tablename__ = "service"
    __table_args__ = (
        Index("ux_service_name_normalized", "name_normalized", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_normalized: Mapped[str] = mapped_column(String(255), nullable=False)
    default_duration_min: Mapped[int] = mapped_column(nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class PatientModel(Base):
    __tablename__ = "patient"
    __table_args__ = (
        CheckConstraint(
            "dni ~ '^[0-9]{7,8}$'",
            name="dni_format",
        ),
        Index("ux_patient_dni", "dni", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dni: Mapped[str] = mapped_column(String(8), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    health_insurance: Mapped[str | None] = mapped_column(String(255), nullable=True)


class WorkingHoursModel(Base):
    __tablename__ = "working_hours"
    __table_args__ = (
        CheckConstraint("weekday >= 1 AND weekday <= 7", name="weekday_range"),
        CheckConstraint(
            "start_minute >= 0 AND end_minute <= 1440 AND start_minute < end_minute",
            name="minute_range",
        ),
        UniqueConstraint(
            "professional_id",
            "weekday",
            "start_minute",
            name="uq_working_hours_professional_weekday_start",
        ),
        Index("ix_working_hours_professional_id_weekday", "professional_id", "weekday"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    professional_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("professional.id"),
        nullable=False,
    )
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    end_minute: Mapped[int] = mapped_column(Integer, nullable=False)


class BlockModel(Base):
    __tablename__ = "block"
    __table_args__ = (
        CheckConstraint("start_at < end_at", name="interval_order"),
        Index(
            "ix_block_professional_id_start_at_end_at",
            "professional_id",
            "start_at",
            "end_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    professional_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("professional.id"),
        nullable=False,
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
