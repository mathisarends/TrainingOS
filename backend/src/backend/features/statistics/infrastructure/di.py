from backend.features.statistics.application import StatisticsService
from dishka import Provider, Scope, provide


class StatisticsProvider(Provider):
    scope = Scope.REQUEST
    service = provide(StatisticsService)
