from dishka import Provider, Scope, provide

from backend.features.sessions.application import SessionService
from backend.features.sessions.domain import SessionRepository
from backend.features.sessions.infrastructure.repository import SqlSessionRepository


class SessionProvider(Provider):
    scope = Scope.REQUEST
    repository = provide(SqlSessionRepository, provides=SessionRepository)
    service = provide(SessionService)
