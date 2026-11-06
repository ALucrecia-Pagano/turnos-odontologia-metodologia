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
    true,
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


class AppointmentModel(Base):
    __tablename__ = "appointment"
    __table_args__ = (
        CheckConstraint(
            "status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')",
            name="status",
        ),
        CheckConstraint("start_at < end_at", name="interval_order"),
        Index("ix_appointment_professional_id_start_at", "professional_id", "start_at"),
        Index("ix_appointment_chair_id_start_at", "chair_id", "start_at"),
        Index("ix_appointment_status_start_at", "status", "start_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    patient_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patient.id", ondelete="RESTRICT"),
        nullable=False,
    )
    professional_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("professional.id", ondelete="RESTRICT"),
        nullable=False,
    )
    chair_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("chair.id", ondelete="RESTRICT"),
        nullable=False,
    )
    service_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("service.id", ondelete="RESTRICT"),
        nullable=False,
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AppointmentStatusChangeModel(Base):
    __tablename__ = "appointment_status_change"
    __table_args__ = (
        CheckConstraint(
            "from_status IS NULL OR from_status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')",
            name="from_status",
        ),
        CheckConstraint(
            "to_status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')",
            name="to_status",
        ),
        CheckConstraint(
            "(reschedule_previous_start_at IS NULL AND reschedule_previous_end_at IS NULL AND "
            "reschedule_new_start_at IS NULL AND reschedule_new_end_at IS NULL AND "
            "reschedule_previous_professional_id IS NULL AND reschedule_new_professional_id IS NULL AND "
            "reschedule_previous_chair_id IS NULL AND reschedule_new_chair_id IS NULL) "
            "OR "
            "(reschedule_previous_start_at IS NOT NULL AND reschedule_previous_end_at IS NOT NULL AND "
            "reschedule_new_start_at IS NOT NULL AND reschedule_new_end_at IS NOT NULL AND "
            "reschedule_previous_professional_id IS NOT NULL AND reschedule_new_professional_id IS NOT NULL AND "
            "reschedule_previous_chair_id IS NOT NULL AND reschedule_new_chair_id IS NOT NULL)",
            name="reschedule_all_or_none",
        ),
        Index(
            "ix_appointment_status_change_appointment_id_changed_at",
            "appointment_id",
            "changed_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    appointment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("appointment.id", ondelete="RESTRICT"),
        nullable=False,
    )
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    reschedule_previous_start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reschedule_previous_end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reschedule_new_start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reschedule_new_end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reschedule_previous_professional_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("professional.id", ondelete="RESTRICT"),
        nullable=True,
    )
    reschedule_new_professional_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("professional.id", ondelete="RESTRICT"),
        nullable=True,
    )
    reschedule_previous_chair_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("chair.id", ondelete="RESTRICT"),
        nullable=True,
    )
    reschedule_new_chair_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("chair.id", ondelete="RESTRICT"),
        nullable=True,
    )


class UserModel(Base):
    __tablename__ = "app_user"
    __table_args__ = (
        CheckConstraint(
            "role IN ('odontologo', 'recepcion', 'administrador')",
            name="role",
        ),
        CheckConstraint(
            "username ~ '^[a-z0-9._-]{3,150}$'",
            name="username_format",
        ),
        CheckConstraint(
            "(role = 'odontologo' AND professional_id IS NOT NULL) "
            "OR (role <> 'odontologo' AND professional_id IS NULL)",
            name="professional_by_role",
        ),
        Index("ux_app_user_username", "username", unique=True),
        Index("ux_app_user_professional_id", "professional_id", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    username: Mapped[str] = mapped_column(String(150), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    professional_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("professional.id", ondelete="RESTRICT"),
        nullable=True,
    )
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=true()
    )
