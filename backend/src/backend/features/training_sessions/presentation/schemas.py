from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import AwareDatetime, Field

from backend.features.exercises.domain import Category
from backend.features.plans.presentation.schemas import PrescriptionResponse
from backend.features.users.domain import EffortScale, WeightUnit
from backend.platform.api.schema import Schema


class StartTrainingSessionRequest(Schema):
    plan_id: UUID
    day_id: UUID
    week: int = Field(ge=1, le=104)


class RecordSetRequest(Schema):
    weight: Decimal = Field(ge=0, le=10000, decimal_places=4)
    reps: int = Field(ge=1, le=100)
    effort: Decimal = Field(ge=0, le=10, multiple_of=0.5)


class SkipSlotRequest(Schema):
    skipped: bool = True


class TimerRequest(Schema):
    delta_seconds: int | None = Field(
        default=None,
        ge=-86400,
        le=86400,
        description="Adjust the absolute deadline; null skips the rest",
    )


class CorrectTrainingSessionRequest(Schema):
    started_at: AwareDatetime
    ended_at: AwareDatetime | None


class WorkSetResponse(Schema):
    id: UUID
    weight: Decimal
    reps: int
    rpe: Decimal
    effort: Decimal
    e1rm: Decimal
    recorded_at: datetime


class TrainingSessionSlotResponse(Schema):
    id: UUID
    exercise_id: UUID
    exercise_name: str
    category: Category
    main: bool
    rest_seconds: int
    prescription: PrescriptionResponse
    skipped: bool
    sets: list[WorkSetResponse]


class TrainingSessionResponse(Schema):
    id: UUID
    plan_id: UUID
    plan_title: str
    day_id: UUID
    day_name: str
    week: int
    unit: WeightUnit
    effort_scale: EffortScale
    slots: list[TrainingSessionSlotResponse]
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None
    server_now: datetime
    rest_ends_at: datetime | None
    rest_remaining_seconds: int


class TrainingSessionListResponse(Schema):
    items: list[TrainingSessionResponse]


class SetFeedbackResponse(Schema):
    training_session: TrainingSessionResponse
    work_set: WorkSetResponse
    backoff_weight: Decimal
    new_personal_record: bool


class GuidanceResponse(Schema):
    unit: WeightUnit
    recommended_weight: Decimal | None
    backoff_weight: Decimal | None
    last_sets: list[WorkSetResponse]
    last_performed_at: datetime | None
