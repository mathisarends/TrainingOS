from dishka import Provider, Scope, provide

from backend.features.statistics.application import StatisticsService


class StatisticsProvider(Provider):
    scope = Scope.REQUEST
    service = provide(StatisticsService)
