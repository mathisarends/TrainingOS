from uuid import UUID

from dishka.integrations.fastapi import FromDishka

from backend.features.auth.presentation import CurrentAthlete
from backend.features.statistics.application import StatisticsService
from backend.platform.api.router import protected_router

from .mapper import to_response
from .schemas import PlanComparisonResponse, StatisticsResponse

router = protected_router(prefix="/statistics", tag="statistics")


@router.get(
    "", operation_id="get_training_statistics", status_code=200, response_model=StatisticsResponse
)
async def training_statistics(
    athlete: CurrentAthlete,
    statistics_service: FromDishka[StatisticsService],
    plan_id: UUID | None = None,
) -> StatisticsResponse:
    statistics = await statistics_service.calculate(
        athlete_id=athlete.id, preferences=athlete.preferences, plan_id=plan_id
    )
    return to_response(statistics, athlete.preferences)


@router.get(
    "/comparison",
    operation_id="compare_training_plans",
    status_code=200,
    response_model=PlanComparisonResponse,
)
async def compare_plans(
    first_plan_id: UUID,
    second_plan_id: UUID,
    athlete: CurrentAthlete,
    statistics_service: FromDishka[StatisticsService],
) -> PlanComparisonResponse:
    first = await statistics_service.calculate(
        athlete_id=athlete.id, preferences=athlete.preferences, plan_id=first_plan_id
    )
    second = await statistics_service.calculate(
        athlete_id=athlete.id, preferences=athlete.preferences, plan_id=second_plan_id
    )
    return PlanComparisonResponse(
        first_plan_id=first_plan_id,
        second_plan_id=second_plan_id,
        first=to_response(first, athlete.preferences),
        second=to_response(second, athlete.preferences),
    )
