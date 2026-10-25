import math
from datetime import UTC, datetime

from backend.features.athletes.domain import EffortScale, Preferences
from backend.features.plans.presentation.mapper import prescription_response
from backend.features.sessions.application import SetFeedback, SlotGuidance
from backend.features.sessions.domain import Session, WorkSet
from backend.features.training.domain import e1rm

from .schemas import (
    GuidanceResponse,
    SessionListResponse,
    SessionResponse,
    SessionSlotResponse,
    SetFeedbackResponse,
    WorkSetResponse,
)


def set_response(item: WorkSet, preferences: Preferences) -> WorkSetResponse:
    maximum = e1rm(weight_kg=item.weight_kg, reps=item.reps, rpe=item.rpe, preferences=preferences)
    return WorkSetResponse(
        id=item.id,
        weight=preferences.from_kg(item.weight_kg),
        reps=item.reps,
        rpe=item.rpe,
        effort=10 - item.rpe if preferences.effort_scale == EffortScale.RIR else item.rpe,
        e1rm=preferences.from_kg(maximum),
        recorded_at=item.recorded_at,
    )


def to_response(session: Session, preferences: Preferences) -> SessionResponse:
    now = datetime.now(UTC)
    remaining = (
        max(0, math.ceil((session.rest_ends_at - now).total_seconds()))
        if session.rest_ends_at
        else 0
    )
    return SessionResponse(
        id=session.id,
        plan_id=session.plan_id,
        plan_title=session.plan_title,
        day_id=session.day_id,
        day_name=session.day_name,
        week=session.week,
        unit=preferences.unit,
        effort_scale=preferences.effort_scale,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=session.duration_seconds,
        server_now=now,
        rest_ends_at=session.rest_ends_at,
        rest_remaining_seconds=remaining,
        slots=[
            SessionSlotResponse(
                id=slot.id,
                exercise_id=slot.exercise_id,
                exercise_name=slot.exercise_name,
                category=slot.category,
                main=slot.main,
                rest_seconds=slot.rest_seconds,
                prescription=prescription_response(slot.prescription, preferences),
                skipped=slot.skipped,
                sets=[set_response(item, preferences) for item in slot.sets],
            )
            for slot in session.slots
        ],
    )


def to_list_response(sessions: list[Session], preferences: Preferences) -> SessionListResponse:
    return SessionListResponse(items=[to_response(session, preferences) for session in sessions])


def to_feedback_response(feedback: SetFeedback, preferences: Preferences) -> SetFeedbackResponse:
    return SetFeedbackResponse(
        session=to_response(feedback.session, preferences),
        work_set=set_response(feedback.work_set, preferences),
        backoff_weight=preferences.from_kg(feedback.backoff_weight_kg),
        new_personal_record=feedback.new_personal_record,
    )


def to_guidance_response(guidance: SlotGuidance, preferences: Preferences) -> GuidanceResponse:
    return GuidanceResponse(
        unit=preferences.unit,
        recommended_weight=preferences.from_kg(guidance.recommended_weight_kg)
        if guidance.recommended_weight_kg is not None
        else None,
        backoff_weight=preferences.from_kg(guidance.backoff_weight_kg)
        if guidance.backoff_weight_kg is not None
        else None,
        last_sets=[set_response(item, preferences) for item in guidance.last_sets],
        last_performed_at=guidance.last_performed_at,
    )
