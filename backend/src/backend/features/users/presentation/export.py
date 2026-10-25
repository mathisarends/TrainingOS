from typing import Literal

from backend.features.bodyweight.presentation.mapper import to_response as weigh_in_response
from backend.features.bodyweight.presentation.schemas import WeighInResponse
from backend.features.exercises.presentation.mapper import to_response as exercise_response
from backend.features.exercises.presentation.schemas import ExerciseResponse
from backend.features.plans.presentation.mapper import to_response as plan_response
from backend.features.plans.presentation.schemas import PlanResponse
from backend.features.training_sessions.presentation.mapper import (
    to_response as training_session_response,
)
from backend.features.training_sessions.presentation.schemas import TrainingSessionResponse
from backend.features.users.application import AccountExport
from backend.platform.api.schema import Schema

from .mapper import to_response
from .schemas import UserResponse


class IdentityExportResponse(Schema):
    issuer: str
    subject: str


class AccountExportResponse(Schema):
    format_version: Literal[2] = 2
    user: UserResponse
    exercises: list[ExerciseResponse]
    plans: list[PlanResponse]
    training_sessions: list[TrainingSessionResponse]
    bodyweight: list[WeighInResponse]
    identities: list[IdentityExportResponse]
    shared_templates: list[PlanResponse]


def to_export_response(export: AccountExport) -> AccountExportResponse:
    preferences = export.user.preferences
    return AccountExportResponse(
        user=to_response(export.user),
        exercises=[exercise_response(item) for item in export.exercises],
        plans=[plan_response(item, preferences) for item in export.plans],
        training_sessions=[
            training_session_response(item, preferences) for item in export.training_sessions
        ],
        bodyweight=[weigh_in_response(item, preferences) for item in export.bodyweight],
        identities=[
            IdentityExportResponse(issuer=item.issuer, subject=item.subject)
            for item in export.identities
        ],
        shared_templates=[plan_response(item, preferences) for item in export.shared_templates],
    )
