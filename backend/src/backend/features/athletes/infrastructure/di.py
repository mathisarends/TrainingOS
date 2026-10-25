from dishka import Provider, Scope, provide

from backend.features.athletes.application import AthleteService
from backend.features.athletes.domain import AthleteRepository
from backend.features.athletes.infrastructure.repository import SqlAthleteRepository


class AthleteProvider(Provider):
    scope = Scope.REQUEST
    repository = provide(SqlAthleteRepository, provides=AthleteRepository)
    service = provide(AthleteService)
