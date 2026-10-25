from dishka import Provider, Scope, provide

from backend.features.training_sessions.application import TrainingSessionService
from backend.features.training_sessions.domain import TrainingSessionRepository
from backend.features.training_sessions.infrastructure.repository import (
    SqlTrainingSessionRepository,
)


class TrainingSessionProvider(Provider):
    scope = Scope.REQUEST
    repository = provide(SqlTrainingSessionRepository, provides=TrainingSessionRepository)
    service = provide(TrainingSessionService)
