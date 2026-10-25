from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import FromDishka
from fastapi import Query

from backend.features.athletes.domain import EffortScale
from backend.features.auth.presentation import CurrentAthlete
from backend.features.sessions.application import SessionService
from backend.features.training.domain import effort_to_rpe
from backend.platform.api.router import protected_router

from .mapper import to_feedback_response, to_guidance_response, to_list_response, to_response
from .schemas import (
    CorrectSessionRequest,
    GuidanceResponse,
    RecordSetRequest,
    SessionListResponse,
    SessionResponse,
    SetFeedbackResponse,
    SkipSlotRequest,
    StartSessionRequest,
    TimerRequest,
)

router = protected_router(prefix="/sessions", tag="sessions")


@router.post("", operation_id="start_session", status_code=201, response_model=SessionResponse)
async def start_session(
    body: StartSessionRequest, athlete: CurrentAthlete, session_service: FromDishka[SessionService]
) -> SessionResponse:
    session = await session_service.start(
        athlete_id=athlete.id, plan_id=body.plan_id, day_id=body.day_id, week=body.week
    )
    return to_response(session, athlete.preferences)


@router.get("", operation_id="list_sessions", status_code=200, response_model=SessionListResponse)
async def list_sessions(
    athlete: CurrentAthlete,
    session_service: FromDishka[SessionService],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> SessionListResponse:
    sessions = await session_service.list(athlete_id=athlete.id, offset=offset, limit=limit)
    return to_list_response(sessions, athlete.preferences)


@router.get(
    "/{session_id}", operation_id="get_session", status_code=200, response_model=SessionResponse
)
async def get_session(
    session_id: UUID, athlete: CurrentAthlete, session_service: FromDishka[SessionService]
) -> SessionResponse:
    session = await session_service.get(athlete_id=athlete.id, session_id=session_id)
    return to_response(session, athlete.preferences)


@router.put(
    "/{session_id}/times",
    operation_id="correct_session_times",
    status_code=200,
    response_model=SessionResponse,
)
async def correct_session_times(
    session_id: UUID,
    body: CorrectSessionRequest,
    athlete: CurrentAthlete,
    session_service: FromDishka[SessionService],
) -> SessionResponse:
    session = await session_service.correct_times(
        athlete_id=athlete.id,
        session_id=session_id,
        started_at=body.started_at,
        ended_at=body.ended_at,
    )
    return to_response(session, athlete.preferences)


@router.post(
    "/{session_id}/finish",
    operation_id="finish_session",
    status_code=200,
    response_model=SessionResponse,
)
async def finish_session(
    session_id: UUID, athlete: CurrentAthlete, session_service: FromDishka[SessionService]
) -> SessionResponse:
    session = await session_service.finish(athlete_id=athlete.id, session_id=session_id)
    return to_response(session, athlete.preferences)


@router.post(
    "/{session_id}/slots/{slot_id}/sets",
    operation_id="record_work_set",
    status_code=201,
    response_model=SetFeedbackResponse,
)
async def record_work_set(
    session_id: UUID,
    slot_id: UUID,
    body: RecordSetRequest,
    athlete: CurrentAthlete,
    session_service: FromDishka[SessionService],
) -> SetFeedbackResponse:
    rpe = effort_to_rpe(body.effort, rir=athlete.preferences.effort_scale == EffortScale.RIR)
    feedback = await session_service.record(
        athlete_id=athlete.id,
        session_id=session_id,
        slot_id=slot_id,
        weight_kg=athlete.preferences.to_kg(body.weight),
        reps=body.reps,
        rpe=rpe,
        preferences=athlete.preferences,
    )
    return to_feedback_response(feedback, athlete.preferences)


@router.put(
    "/{session_id}/slots/{slot_id}/sets/{set_id}",
    operation_id="correct_work_set",
    status_code=200,
    response_model=SetFeedbackResponse,
)
async def correct_work_set(
    session_id: UUID,
    slot_id: UUID,
    set_id: UUID,
    body: RecordSetRequest,
    athlete: CurrentAthlete,
    session_service: FromDishka[SessionService],
) -> SetFeedbackResponse:
    rpe = effort_to_rpe(body.effort, rir=athlete.preferences.effort_scale == EffortScale.RIR)
    feedback = await session_service.record(
        athlete_id=athlete.id,
        session_id=session_id,
        slot_id=slot_id,
        set_id=set_id,
        weight_kg=athlete.preferences.to_kg(body.weight),
        reps=body.reps,
        rpe=rpe,
        preferences=athlete.preferences,
    )
    return to_feedback_response(feedback, athlete.preferences)


@router.delete(
    "/{session_id}/slots/{slot_id}/sets/{set_id}",
    operation_id="delete_work_set",
    status_code=200,
    response_model=SessionResponse,
)
async def delete_work_set(
    session_id: UUID,
    slot_id: UUID,
    set_id: UUID,
    athlete: CurrentAthlete,
    session_service: FromDishka[SessionService],
) -> SessionResponse:
    session = await session_service.remove_set(
        athlete_id=athlete.id, session_id=session_id, slot_id=slot_id, set_id=set_id
    )
    return to_response(session, athlete.preferences)


@router.put(
    "/{session_id}/slots/{slot_id}/skipped",
    operation_id="skip_session_slot",
    status_code=200,
    response_model=SessionResponse,
)
async def skip_slot(
    session_id: UUID,
    slot_id: UUID,
    body: SkipSlotRequest,
    athlete: CurrentAthlete,
    session_service: FromDishka[SessionService],
) -> SessionResponse:
    session = await session_service.skip(
        athlete_id=athlete.id, session_id=session_id, slot_id=slot_id, skipped=body.skipped
    )
    return to_response(session, athlete.preferences)


@router.get(
    "/{session_id}/slots/{slot_id}/guidance",
    operation_id="get_slot_guidance",
    status_code=200,
    response_model=GuidanceResponse,
)
async def slot_guidance(
    session_id: UUID,
    slot_id: UUID,
    athlete: CurrentAthlete,
    session_service: FromDishka[SessionService],
) -> GuidanceResponse:
    guidance = await session_service.guidance(
        athlete_id=athlete.id,
        session_id=session_id,
        slot_id=slot_id,
        preferences=athlete.preferences,
    )
    return to_guidance_response(guidance, athlete.preferences)


@router.put(
    "/{session_id}/timer",
    operation_id="adjust_rest_timer",
    status_code=200,
    response_model=SessionResponse,
)
async def adjust_timer(
    session_id: UUID,
    body: TimerRequest,
    athlete: CurrentAthlete,
    session_service: FromDishka[SessionService],
) -> SessionResponse:
    session = await session_service.timer(
        athlete_id=athlete.id, session_id=session_id, delta_seconds=body.delta_seconds
    )
    return to_response(session, athlete.preferences)
