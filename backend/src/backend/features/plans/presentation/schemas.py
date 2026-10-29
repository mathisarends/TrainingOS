from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from backend.features.exercises.domain import Category
from backend.features.plans.domain import PlanStatus
from backend.platform.api.schema import Schema


class DayRequest(Schema):
    name: str = Field(min_length=1, max_length=200)
    weekday: int = Field(ge=0, le=6, description="Monday=0, Sunday=6")


class CreatePlanRequest(Schema):
    title: str = Field(min_length=1, max_length=200)
    start_date: date
    weeks: int = Field(ge=1, le=104)
    days: list[DayRequest] = Field(min_length=1, max_length=14)


class ConfigurePlanRequest(Schema):
    title: str = Field(min_length=1, max_length=200)
    start_date: date
    recommendations: bool


class DuplicatePlanRequest(Schema):
    title: str = Field(min_length=1, max_length=200)
    start_date: date


class StatusRequest(Schema):
    status: PlanStatus


class AddSlotRequest(Schema):
    exercise_id: UUID
    rest_seconds: int | None = Field(default=None, ge=0, le=3600)


class EditSlotRequest(Schema):
    rest_seconds: int = Field(ge=0, le=3600)


class ReorderSlotsRequest(Schema):
    slot_ids: list[UUID] = Field(max_length=100)


class PrescriptionRequest(Schema):
    sets: int = Field(ge=1, le=100)
    reps: int = Field(ge=1, le=100)
    target_effort: Decimal = Field(ge=0, le=10, multiple_of=0.5)
    note: str = Field(default="", max_length=2000)


class ProgressionRequest(Schema):
    increment: Decimal = Field(default=Decimal("0.5"))
    deload: bool = False


class ApplyProgressionRequest(ProgressionRequest):
    expected_revision: int = Field(ge=1)


class PrescriptionResponse(Schema):
    week: int
    sets: int
    reps: int
    target_rpe: Decimal
    target_effort: Decimal
    note: str


class SlotResponse(Schema):
    id: UUID
    exercise_id: UUID
    exercise_name: str
    category: Category
    main: bool
    rest_seconds: int
    prescriptions: list[PrescriptionResponse]


class DayResponse(Schema):
    id: UUID
    name: str
    weekday: int
    slots: list[SlotResponse]


class PlanResponse(Schema):
    id: UUID
    title: str
    start_date: date
    weeks: int
    status: PlanStatus
    recommendations: bool
    revision: int
    days: list[DayResponse]


class PlanListResponse(Schema):
    items: list[PlanResponse]


class ShareResponse(Schema):
    token: str


class NextTrainingResponse(Schema):
    plan_id: UUID | None = None
    day_id: UUID | None = None
    week: int | None = None
    scheduled_date: date | None = None
    running_training_session_id: UUID | None = None


class ProgressionPreviewResponse(Schema):
    base_revision: int
    plan: PlanResponse
