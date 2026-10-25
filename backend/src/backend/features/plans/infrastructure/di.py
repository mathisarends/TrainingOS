from dishka import Provider, Scope, provide

from backend.features.plans.application import PlanService
from backend.features.plans.domain import PlanRepository
from backend.features.plans.infrastructure.repository import SqlPlanRepository


class PlanProvider(Provider):
    scope = Scope.REQUEST
    repository = provide(SqlPlanRepository, provides=PlanRepository)
    service = provide(PlanService)
