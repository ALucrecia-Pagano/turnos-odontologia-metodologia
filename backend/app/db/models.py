from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Index, String, Uuid
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
