from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import FromDishka
from fastapi import Query

from backend.features.auth.presentation import CurrentUser
from backend.features.training.domain import effort_to_rpe
from backend.features.training_sessions.application import TrainingSessionService
from backend.features.users.domain import EffortScale
from backend.platform.api.router import protected_router

from .mapper import to_feedback_response, to_guidance_response, to_list_response, to_response
from .schemas import (
    CorrectTrainingSessionRequest,
    GuidanceResponse,
    RecordSetRequest,
    SetFeedbackResponse,
    SkipSlotRequest,
    StartTrainingSessionRequest,
    TimerRequest,
    TrainingSessionListResponse,
    TrainingSessionResponse,
)

router = protected_router(prefix="/training-sessions", tag="training-sessions")


@router.post(
    "",
    operation_id="start_training_session",
    status_code=201,
    response_model=TrainingSessionResponse,
)
async def start_training_session(
    body: StartTrainingSessionRequest,
    user: CurrentUser,
    training_session_service: FromDishka[TrainingSessionService],
) -> TrainingSessionResponse:
    training_session = await training_session_service.start(
        user_id=user.id, plan_id=body.plan_id, day_id=body.day_id, week=body.week
    )
    return to_response(training_session, user.preferences)


@router.get(
    "",
    operation_id="list_training_sessions",
    status_code=200,
    response_model=TrainingSessionListResponse,
)
async def list_training_sessions(
    user: CurrentUser,
    training_session_service: FromDishka[TrainingSessionService],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> TrainingSessionListResponse:
    training_sessions = await training_session_service.list(
        user_id=user.id, offset=offset, limit=limit
    )
    return to_list_response(training_sessions, user.preferences)


@router.get(
    "/{training_session_id}",
    operation_id="get_training_session",
    status_code=200,
    response_model=TrainingSessionResponse,
)
async def get_training_session(
    training_session_id: UUID,
    user: CurrentUser,
    training_session_service: FromDishka[TrainingSessionService],
) -> TrainingSessionResponse:
    training_session = await training_session_service.get(
        user_id=user.id, training_session_id=training_session_id
    )
    return to_response(training_session, user.preferences)


@router.put(
    "/{training_session_id}/times",
    operation_id="correct_training_session_times",
    status_code=200,
    response_model=TrainingSessionResponse,
)
async def correct_training_session_times(
    training_session_id: UUID,
    body: CorrectTrainingSessionRequest,
    user: CurrentUser,
    training_session_service: FromDishka[TrainingSessionService],
) -> TrainingSessionResponse:
    training_session = await training_session_service.correct_times(
        user_id=user.id,
        training_session_id=training_session_id,
        started_at=body.started_at,
        ended_at=body.ended_at,
    )
    return to_response(training_session, user.preferences)


@router.post(
    "/{training_session_id}/finish",
    operation_id="finish_training_session",
    status_code=200,
    response_model=TrainingSessionResponse,
)
async def finish_training_session(
    training_session_id: UUID,
    user: CurrentUser,
    training_session_service: FromDishka[TrainingSessionService],
) -> TrainingSessionResponse:
    training_session = await training_session_service.finish(
        user_id=user.id, training_session_id=training_session_id
    )
    return to_response(training_session, user.preferences)


@router.post(
    "/{training_session_id}/slots/{slot_id}/sets",
    operation_id="record_work_set",
    status_code=201,
    response_model=SetFeedbackResponse,
)
async def record_work_set(
    training_session_id: UUID,
    slot_id: UUID,
    body: RecordSetRequest,
    user: CurrentUser,
    training_session_service: FromDishka[TrainingSessionService],
) -> SetFeedbackResponse:
    rpe = effort_to_rpe(body.effort, rir=user.preferences.effort_scale == EffortScale.RIR)
    feedback = await training_session_service.record(
        user_id=user.id,
        training_session_id=training_session_id,
        slot_id=slot_id,
        weight_kg=user.preferences.to_kg(body.weight),
        reps=body.reps,
        rpe=rpe,
        preferences=user.preferences,
    )
    return to_feedback_response(feedback, user.preferences)


@router.put(
    "/{training_session_id}/slots/{slot_id}/sets/{set_id}",
    operation_id="correct_work_set",
    status_code=200,
    response_model=SetFeedbackResponse,
)
async def correct_work_set(
    training_session_id: UUID,
    slot_id: UUID,
    set_id: UUID,
    body: RecordSetRequest,
    user: CurrentUser,
    training_session_service: FromDishka[TrainingSessionService],
) -> SetFeedbackResponse:
    rpe = effort_to_rpe(body.effort, rir=user.preferences.effort_scale == EffortScale.RIR)
    feedback = await training_session_service.record(
        user_id=user.id,
        training_session_id=training_session_id,
        slot_id=slot_id,
        set_id=set_id,
        weight_kg=user.preferences.to_kg(body.weight),
        reps=body.reps,
        rpe=rpe,
        preferences=user.preferences,
    )
    return to_feedback_response(feedback, user.preferences)


@router.delete(
    "/{training_session_id}/slots/{slot_id}/sets/{set_id}",
    operation_id="delete_work_set",
    status_code=200,
    response_model=TrainingSessionResponse,
)
async def delete_work_set(
    training_session_id: UUID,
    slot_id: UUID,
    set_id: UUID,
    user: CurrentUser,
    training_session_service: FromDishka[TrainingSessionService],
) -> TrainingSessionResponse:
    training_session = await training_session_service.remove_set(
        user_id=user.id, training_session_id=training_session_id, slot_id=slot_id, set_id=set_id
    )
    return to_response(training_session, user.preferences)


@router.put(
    "/{training_session_id}/slots/{slot_id}/skipped",
    operation_id="skip_training_session_slot",
    status_code=200,
    response_model=TrainingSessionResponse,
)
async def skip_slot(
    training_session_id: UUID,
    slot_id: UUID,
    body: SkipSlotRequest,
    user: CurrentUser,
    training_session_service: FromDishka[TrainingSessionService],
) -> TrainingSessionResponse:
    training_session = await training_session_service.skip(
        user_id=user.id,
        training_session_id=training_session_id,
        slot_id=slot_id,
        skipped=body.skipped,
    )
    return to_response(training_session, user.preferences)


@router.get(
    "/{training_session_id}/slots/{slot_id}/guidance",
    operation_id="get_slot_guidance",
    status_code=200,
    response_model=GuidanceResponse,
)
async def slot_guidance(
    training_session_id: UUID,
    slot_id: UUID,
    user: CurrentUser,
    training_session_service: FromDishka[TrainingSessionService],
) -> GuidanceResponse:
    guidance = await training_session_service.guidance(
        user_id=user.id,
        training_session_id=training_session_id,
        slot_id=slot_id,
        preferences=user.preferences,
    )
    return to_guidance_response(guidance, user.preferences)


@router.put(
    "/{training_session_id}/timer",
    operation_id="adjust_rest_timer",
    status_code=200,
    response_model=TrainingSessionResponse,
)
async def adjust_timer(
    training_session_id: UUID,
    body: TimerRequest,
    user: CurrentUser,
    training_session_service: FromDishka[TrainingSessionService],
) -> TrainingSessionResponse:
    training_session = await training_session_service.timer(
        user_id=user.id, training_session_id=training_session_id, delta_seconds=body.delta_seconds
    )
    return to_response(training_session, user.preferences)
