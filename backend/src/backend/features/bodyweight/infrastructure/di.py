from dishka import Provider, Scope, provide

from backend.features.bodyweight.application import BodyweightService
from backend.features.bodyweight.domain import BodyweightRepository
from backend.features.bodyweight.infrastructure.repository import SqlBodyweightRepository


class BodyweightProvider(Provider):
    scope = Scope.REQUEST
    repository = provide(SqlBodyweightRepository, provides=BodyweightRepository)
    service = provide(BodyweightService)
