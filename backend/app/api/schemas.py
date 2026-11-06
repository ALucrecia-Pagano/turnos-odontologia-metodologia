from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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

