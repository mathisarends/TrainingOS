from backend.features.athletes.domain import EffortScale, Preferences
from backend.features.plans.application import NextTraining
from backend.features.plans.domain import Plan, Prescription

from .schemas import (
    DayResponse,
    NextTrainingResponse,
    PlanListResponse,
    PlanResponse,
    PrescriptionResponse,
    SlotResponse,
)


def prescription_response(
    prescription: Prescription, preferences: Preferences
) -> PrescriptionResponse:
    return PrescriptionResponse(
        week=prescription.week,
        sets=prescription.sets,
        reps=prescription.reps,
        target_rpe=prescription.target_rpe,
        target_effort=10 - prescription.target_rpe
        if preferences.effort_scale == EffortScale.RIR
        else prescription.target_rpe,
        note=prescription.note,
    )


def to_response(plan: Plan, preferences: Preferences) -> PlanResponse:
    return PlanResponse(
        id=plan.id,
        title=plan.title,
        start_date=plan.start_date,
        weeks=plan.weeks,
        status=plan.status,
        recommendations=plan.recommendations,
        revision=plan.revision,
        days=[
            DayResponse(
                id=day.id,
                name=day.name,
                weekday=day.weekday,
                slots=[
                    SlotResponse(
                        id=slot.id,
                        exercise_id=slot.exercise_id,
                        exercise_name=slot.exercise_name,
                        category=slot.category,
                        main=slot.main,
                        rest_seconds=slot.rest_seconds,
                        prescriptions=[
                            prescription_response(item, preferences) for item in slot.prescriptions
                        ],
                    )
                    for slot in day.slots
                ],
            )
            for day in plan.days
        ],
    )


def to_list_response(plans: list[Plan], preferences: Preferences) -> PlanListResponse:
    return PlanListResponse(items=[to_response(plan, preferences) for plan in plans])


def to_next_response(training: NextTraining | None) -> NextTrainingResponse:
    if training is None:
        return NextTrainingResponse()
    return NextTrainingResponse(
        plan_id=training.plan_id,
        day_id=training.day_id,
        week=training.week,
        scheduled_date=training.scheduled_date,
        running_session_id=training.running_session_id,
    )
