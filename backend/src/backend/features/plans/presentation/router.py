from uuid import UUID

from dishka.integrations.fastapi import FromDishka
from fastapi import Response

from backend.features.auth.presentation import CurrentUser
from backend.features.plans.application import DayDefinition, PlanService
from backend.features.plans.domain import Prescription
from backend.features.training.domain import effort_to_rpe
from backend.features.users.domain import EffortScale
from backend.platform.api.router import protected_router

from .mapper import to_list_response, to_next_response, to_response
from .schemas import (
    AddSlotRequest,
    ApplyProgressionRequest,
    ConfigurePlanRequest,
    CreatePlanRequest,
    DayRequest,
    DuplicatePlanRequest,
    EditSlotRequest,
    NextTrainingResponse,
    PlanListResponse,
    PlanResponse,
    PrescriptionRequest,
    ProgressionPreviewResponse,
    ProgressionRequest,
    ReorderSlotsRequest,
    ShareResponse,
    StatusRequest,
)

router = protected_router(prefix="/plans", tag="plans")


@router.get("", operation_id="list_plans", status_code=200, response_model=PlanListResponse)
async def list_plans(user: CurrentUser, plan_service: FromDishka[PlanService]) -> PlanListResponse:
    plans = await plan_service.list(user_id=user.id)
    return to_list_response(plans, user.preferences)


@router.get(
    "/next-training",
    operation_id="get_next_training",
    status_code=200,
    response_model=NextTrainingResponse,
)
async def next_training(
    user: CurrentUser, plan_service: FromDishka[PlanService]
) -> NextTrainingResponse:
    training = await plan_service.next_training(user_id=user.id)
    return to_next_response(training)


@router.post("", operation_id="create_plan", status_code=201, response_model=PlanResponse)
async def create_plan(
    body: CreatePlanRequest, user: CurrentUser, plan_service: FromDishka[PlanService]
) -> PlanResponse:
    days = tuple(DayDefinition(name=day.name, weekday=day.weekday) for day in body.days)
    plan = await plan_service.create(
        user_id=user.id,
        title=body.title,
        start_date=body.start_date,
        weeks=body.weeks,
        days=days,
    )
    return to_response(plan, user.preferences)


@router.get("/{plan_id}", operation_id="get_plan", status_code=200, response_model=PlanResponse)
async def get_plan(
    plan_id: UUID, user: CurrentUser, plan_service: FromDishka[PlanService]
) -> PlanResponse:
    plan = await plan_service.get(user_id=user.id, plan_id=plan_id)
    return to_response(plan, user.preferences)


@router.put(
    "/{plan_id}", operation_id="configure_plan", status_code=200, response_model=PlanResponse
)
async def configure_plan(
    plan_id: UUID,
    body: ConfigurePlanRequest,
    user: CurrentUser,
    plan_service: FromDishka[PlanService],
) -> PlanResponse:
    plan = await plan_service.configure(
        user_id=user.id,
        plan_id=plan_id,
        title=body.title,
        start_date=body.start_date,
        recommendations=body.recommendations,
    )
    return to_response(plan, user.preferences)


@router.put(
    "/{plan_id}/status",
    operation_id="set_plan_status",
    status_code=200,
    response_model=PlanResponse,
)
async def set_plan_status(
    plan_id: UUID,
    body: StatusRequest,
    user: CurrentUser,
    plan_service: FromDishka[PlanService],
) -> PlanResponse:
    plan = await plan_service.set_status(user_id=user.id, plan_id=plan_id, status=body.status)
    return to_response(plan, user.preferences)


@router.delete("/{plan_id}", operation_id="delete_plan", status_code=204, response_model=None)
async def delete_plan(
    plan_id: UUID, user: CurrentUser, plan_service: FromDishka[PlanService]
) -> Response:
    await plan_service.remove(user_id=user.id, plan_id=plan_id)
    return Response(status_code=204)


@router.put(
    "/{plan_id}/days/{day_id}",
    operation_id="edit_training_day",
    status_code=200,
    response_model=PlanResponse,
)
async def edit_day(
    plan_id: UUID,
    day_id: UUID,
    body: DayRequest,
    user: CurrentUser,
    plan_service: FromDishka[PlanService],
) -> PlanResponse:
    definition = DayDefinition(name=body.name, weekday=body.weekday)
    plan = await plan_service.edit_day(
        user_id=user.id, plan_id=plan_id, day_id=day_id, definition=definition
    )
    return to_response(plan, user.preferences)


@router.post(
    "/{plan_id}/days/{day_id}/slots",
    operation_id="add_exercise_slot",
    status_code=201,
    response_model=PlanResponse,
)
async def add_slot(
    plan_id: UUID,
    day_id: UUID,
    body: AddSlotRequest,
    user: CurrentUser,
    plan_service: FromDishka[PlanService],
) -> PlanResponse:
    plan = await plan_service.add_slot(
        user_id=user.id,
        plan_id=plan_id,
        day_id=day_id,
        exercise_id=body.exercise_id,
        rest_seconds=body.rest_seconds,
    )
    return to_response(plan, user.preferences)


@router.put(
    "/{plan_id}/days/{day_id}/slot-order",
    operation_id="reorder_exercise_slots",
    status_code=200,
    response_model=PlanResponse,
)
async def reorder_slots(
    plan_id: UUID,
    day_id: UUID,
    body: ReorderSlotsRequest,
    user: CurrentUser,
    plan_service: FromDishka[PlanService],
) -> PlanResponse:
    plan = await plan_service.reorder(
        user_id=user.id, plan_id=plan_id, day_id=day_id, slot_ids=tuple(body.slot_ids)
    )
    return to_response(plan, user.preferences)


@router.put(
    "/{plan_id}/days/{day_id}/slots/{slot_id}",
    operation_id="edit_exercise_slot",
    status_code=200,
    response_model=PlanResponse,
)
async def edit_slot(
    plan_id: UUID,
    day_id: UUID,
    slot_id: UUID,
    body: EditSlotRequest,
    user: CurrentUser,
    plan_service: FromDishka[PlanService],
) -> PlanResponse:
    plan = await plan_service.edit_slot(
        user_id=user.id,
        plan_id=plan_id,
        day_id=day_id,
        slot_id=slot_id,
        rest_seconds=body.rest_seconds,
    )
    return to_response(plan, user.preferences)


@router.delete(
    "/{plan_id}/days/{day_id}/slots/{slot_id}",
    operation_id="remove_exercise_slot",
    status_code=200,
    response_model=PlanResponse,
)
async def remove_slot(
    plan_id: UUID,
    day_id: UUID,
    slot_id: UUID,
    user: CurrentUser,
    plan_service: FromDishka[PlanService],
) -> PlanResponse:
    plan = await plan_service.edit_slot(
        user_id=user.id, plan_id=plan_id, day_id=day_id, slot_id=slot_id, rest_seconds=None
    )
    return to_response(plan, user.preferences)


@router.put(
    "/{plan_id}/slots/{slot_id}/weeks/{week}",
    operation_id="set_week_prescription",
    status_code=200,
    response_model=PlanResponse,
)
async def prescribe(
    plan_id: UUID,
    slot_id: UUID,
    week: int,
    body: PrescriptionRequest,
    user: CurrentUser,
    plan_service: FromDishka[PlanService],
) -> PlanResponse:
    target_rpe = effort_to_rpe(
        body.target_effort, rir=user.preferences.effort_scale == EffortScale.RIR
    )
    prescription = Prescription(
        week=week, sets=body.sets, reps=body.reps, target_rpe=target_rpe, note=body.note
    )
    plan = await plan_service.prescribe(
        user_id=user.id, plan_id=plan_id, slot_id=slot_id, prescription=prescription
    )
    return to_response(plan, user.preferences)


@router.post(
    "/{plan_id}/weeks/{week}/copy-forward",
    operation_id="copy_week_forward",
    status_code=200,
    response_model=PlanResponse,
)
async def copy_week(
    plan_id: UUID, week: int, user: CurrentUser, plan_service: FromDishka[PlanService]
) -> PlanResponse:
    plan = await plan_service.copy_week(user_id=user.id, plan_id=plan_id, week=week)
    return to_response(plan, user.preferences)


@router.post(
    "/{plan_id}/progression/preview",
    operation_id="preview_progression",
    status_code=200,
    response_model=ProgressionPreviewResponse,
)
async def preview_progression(
    plan_id: UUID,
    body: ProgressionRequest,
    user: CurrentUser,
    plan_service: FromDishka[PlanService],
) -> ProgressionPreviewResponse:
    original = await plan_service.get(user_id=user.id, plan_id=plan_id)
    preview = await plan_service.progression(
        user_id=user.id, plan_id=plan_id, increment=body.increment, deload=body.deload
    )
    return ProgressionPreviewResponse(
        base_revision=original.revision, plan=to_response(preview, user.preferences)
    )


@router.post(
    "/{plan_id}/progression/apply",
    operation_id="apply_progression",
    status_code=200,
    response_model=PlanResponse,
)
async def apply_progression(
    plan_id: UUID,
    body: ApplyProgressionRequest,
    user: CurrentUser,
    plan_service: FromDishka[PlanService],
) -> PlanResponse:
    plan = await plan_service.progression(
        user_id=user.id,
        plan_id=plan_id,
        increment=body.increment,
        deload=body.deload,
        expected_revision=body.expected_revision,
    )
    return to_response(plan, user.preferences)


@router.post(
    "/{plan_id}/duplicate",
    operation_id="duplicate_plan",
    status_code=201,
    response_model=PlanResponse,
)
async def duplicate_plan(
    plan_id: UUID,
    body: DuplicatePlanRequest,
    user: CurrentUser,
    plan_service: FromDishka[PlanService],
) -> PlanResponse:
    plan = await plan_service.duplicate(
        user_id=user.id, plan_id=plan_id, title=body.title, start_date=body.start_date
    )
    return to_response(plan, user.preferences)


@router.post(
    "/{plan_id}/shares",
    operation_id="share_plan_template",
    status_code=201,
    response_model=ShareResponse,
)
async def share_plan(
    plan_id: UUID, user: CurrentUser, plan_service: FromDishka[PlanService]
) -> ShareResponse:
    token = await plan_service.share(user_id=user.id, plan_id=plan_id)
    return ShareResponse(token=token)


templates_router = protected_router(prefix="/templates", tag="plans")


@templates_router.post(
    "/{token}/import",
    operation_id="import_plan_template",
    status_code=201,
    response_model=PlanResponse,
)
async def import_template(
    token: str,
    body: DuplicatePlanRequest,
    user: CurrentUser,
    plan_service: FromDishka[PlanService],
) -> PlanResponse:
    plan = await plan_service.import_template(
        user_id=user.id, token=token, title=body.title, start_date=body.start_date
    )
    return to_response(plan, user.preferences)


@templates_router.delete(
    "/{token}", operation_id="revoke_plan_template", status_code=204, response_model=None
)
async def revoke_template(
    token: str, user: CurrentUser, plan_service: FromDishka[PlanService]
) -> Response:
    await plan_service.revoke_share(user_id=user.id, token=token)
    return Response(status_code=204)
