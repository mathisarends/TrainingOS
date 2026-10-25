from typing import Literal

from backend.features.athletes.application import AccountExport
from backend.features.bodyweight.presentation.mapper import to_response as weigh_in_response
from backend.features.bodyweight.presentation.schemas import WeighInResponse
from backend.features.exercises.presentation.mapper import to_response as exercise_response
from backend.features.exercises.presentation.schemas import ExerciseResponse
from backend.features.plans.presentation.mapper import to_response as plan_response
from backend.features.plans.presentation.schemas import PlanResponse
from backend.features.sessions.presentation.mapper import to_response as session_response
from backend.features.sessions.presentation.schemas import SessionResponse
from backend.platform.api.schema import Schema

from .mapper import to_response
from .schemas import AthleteResponse


class AccountExportResponse(Schema):
    format_version: Literal[1] = 1
    athlete: AthleteResponse
    exercises: list[ExerciseResponse]
    plans: list[PlanResponse]
    sessions: list[SessionResponse]
    bodyweight: list[WeighInResponse]


def to_export_response(export: AccountExport) -> AccountExportResponse:
    preferences = export.athlete.preferences
    return AccountExportResponse(
        athlete=to_response(export.athlete),
        exercises=[exercise_response(item) for item in export.exercises],
        plans=[plan_response(item, preferences) for item in export.plans],
        sessions=[session_response(item, preferences) for item in export.sessions],
        bodyweight=[weigh_in_response(item, preferences) for item in export.bodyweight],
    )
