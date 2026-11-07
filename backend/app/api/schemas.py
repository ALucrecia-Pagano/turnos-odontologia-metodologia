from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Final
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.intervals import Interval
from app.domain.violations import ReferenceKind, Violation, ViolationCode


def format_utc_iso(dt: datetime) -> str:
    utc_dt = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class IntervalSchema(BaseModel):
    start_at: str = Field(serialization_alias="startAt")
    end_at: str = Field(serialization_alias="endAt")

    model_config = ConfigDict(populate_by_name=True)


class ViolationItemSchema(BaseModel):
    code: ViolationCode
    message: str
    conflicting_appointment_id: UUID | None = Field(default=None, serialization_alias="conflictingAppointmentId")
    conflicting_block_id: UUID | None = Field(default=None, serialization_alias="conflictingBlockId")
    conflicting_interval: IntervalSchema | None = Field(default=None, serialization_alias="conflictingInterval")
    reference_kind: ReferenceKind | None = Field(default=None, serialization_alias="referenceKind")

    model_config = ConfigDict(populate_by_name=True)


class ViolationResponseSchema(BaseModel):
    violations: list[ViolationItemSchema]


class MalformedErrorItem(BaseModel):
    field: str | None
    type: str
    message: str


class MalformedRequestResponse(BaseModel):
    errors: list[MalformedErrorItem]


class AuthErrorCode(str, Enum):
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_TOKEN = "INVALID_TOKEN"


class AuthErrorResponse(BaseModel):
    code: AuthErrorCode
    message: str


class HealthResponse(BaseModel):
    status: str
    database: str


class NotFoundErrorResponse(BaseModel):
    code: str = "NOT_FOUND"
    message: str


class ProfessionalInput(BaseModel):
    full_name: str = Field(alias="fullName")
    license_number: str | None = Field(default=None, alias="licenseNumber")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class ChairInput(BaseModel):
    name: str

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class ServiceInput(BaseModel):
    name: str
    default_duration_min: int = Field(alias="defaultDurationMin")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class PatientInput(BaseModel):
    full_name: str = Field(alias="fullName")
    dni: str
    phone: str | None = None
    health_insurance: str | None = Field(default=None, alias="healthInsurance")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class ProfessionalResponse(BaseModel):
    id: UUID
    full_name: str = Field(serialization_alias="fullName")
    active: bool
    license_number: str | None = Field(default=None, serialization_alias="licenseNumber")

    model_config = ConfigDict(populate_by_name=True)


class ChairResponse(BaseModel):
    id: UUID
    name: str
    active: bool

    model_config = ConfigDict(populate_by_name=True)


class ServiceResponse(BaseModel):
    id: UUID
    name: str
    default_duration_min: int = Field(serialization_alias="defaultDurationMin")
    active: bool

    model_config = ConfigDict(populate_by_name=True)


class PatientResponse(BaseModel):
    id: UUID
    full_name: str = Field(serialization_alias="fullName")
    dni: str
    phone: str | None = None
    health_insurance: str | None = Field(default=None, serialization_alias="healthInsurance")

    model_config = ConfigDict(populate_by_name=True)



def serialize_violation(v: Violation) -> dict[str, Any]:
    interval_schema: IntervalSchema | None = None
    if v.conflicting_interval is not None:
        interval_schema = IntervalSchema(
            start_at=format_utc_iso(v.conflicting_interval.start),
            end_at=format_utc_iso(v.conflicting_interval.end),
        )

    item = ViolationItemSchema(
        code=v.code,
        message=v.message,
        conflicting_appointment_id=v.conflicting_appointment_id,
        conflicting_block_id=v.conflicting_block_id,
        conflicting_interval=interval_schema,
        reference_kind=v.reference_kind,
    )
    return item.model_dump(by_alias=True, exclude_none=True, mode="json")


_START_TIME_REGEX: Final = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
_END_TIME_REGEX: Final = re.compile(r"^(?:(?:[01]\d|2[0-3]):[0-5]\d|24:00)$")


class WorkingHoursSlotInput(BaseModel):
    weekday: int
    start: str
    end: str

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator("weekday")
    @classmethod
    def validate_weekday(cls, v: int) -> int:
        if not (1 <= v <= 7):
            raise ValueError("El día de la semana debe estar entre 1 y 7.")
        return v

    @field_validator("start")
    @classmethod
    def validate_start(cls, v: str) -> str:
        if not _START_TIME_REGEX.match(v):
            raise ValueError("start debe tener formato HH:MM válido (00:00 a 23:59).")
        return v

    @field_validator("end")
    @classmethod
    def validate_end(cls, v: str) -> str:
        if not _END_TIME_REGEX.match(v):
            raise ValueError("end debe tener formato HH:MM válido (00:00 a 24:00).")
        return v


class WorkingHoursSlotResponse(BaseModel):
    weekday: int
    start: str
    end: str

    model_config = ConfigDict(populate_by_name=True)


class AffectedAppointmentResponse(BaseModel):
    id: UUID
    patient_id: UUID = Field(serialization_alias="patientId")
    patient_name: str = Field(serialization_alias="patientName")
    chair_id: UUID = Field(serialization_alias="chairId")
    start_at: str = Field(serialization_alias="startAt")
    end_at: str = Field(serialization_alias="endAt")
    status: str

    model_config = ConfigDict(populate_by_name=True)


class WorkingHoursResponse(BaseModel):
    working_hours: list[WorkingHoursSlotResponse] = Field(serialization_alias="workingHours")
    appointments_outside_hours: list[AffectedAppointmentResponse] = Field(
        serialization_alias="appointmentsOutsideHours"
    )

    model_config = ConfigDict(populate_by_name=True)


class BlockInput(BaseModel):
    start_at: datetime = Field(alias="startAt")
    end_at: datetime = Field(alias="endAt")
    reason: str | None = None

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator("start_at", "end_at")
    @classmethod
    def validate_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("La fecha y hora debe incluir zona horaria.")
        return v


class BlockResponse(BaseModel):
    id: UUID
    professional_id: UUID = Field(serialization_alias="professionalId")
    start_at: str = Field(serialization_alias="startAt")
    end_at: str = Field(serialization_alias="endAt")
    reason: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class BlockCreateResponse(BaseModel):
    block: BlockResponse
    affected_appointments: list[AffectedAppointmentResponse] = Field(
        serialization_alias="affectedAppointments"
    )

    model_config = ConfigDict(populate_by_name=True)


class BlocksQuery(BaseModel):
    from_time: datetime | None = Field(default=None, alias="from")
    to_time: datetime | None = Field(default=None, alias="to")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator("from_time", "to_time")
    @classmethod
    def validate_tz(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            raise ValueError("La fecha y hora debe incluir zona horaria.")
        return v


class AppointmentInput(BaseModel):
    patient_id: UUID = Field(alias="patientId")
    professional_id: UUID = Field(alias="professionalId")
    chair_id: UUID = Field(alias="chairId")
    service_id: UUID = Field(alias="serviceId")
    start_at: datetime = Field(alias="startAt")
    duration_min: int | None = Field(default=None, alias="durationMin")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator("start_at")
    @classmethod
    def validate_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("La fecha y hora debe incluir zona horaria.")
        return v


class AppointmentResponse(BaseModel):
    id: UUID
    patient_id: UUID = Field(serialization_alias="patientId")
    professional_id: UUID = Field(serialization_alias="professionalId")
    chair_id: UUID = Field(serialization_alias="chairId")
    service_id: UUID = Field(serialization_alias="serviceId")
    start_at: str = Field(serialization_alias="startAt")
    end_at: str = Field(serialization_alias="endAt")
    status: str

    model_config = ConfigDict(populate_by_name=True)

