from dishka import Provider, Scope, provide

from backend.features.users.application import UserService
from backend.features.users.domain import UserRepository
from backend.features.users.infrastructure.repository import SqlUserRepository


class UserProvider(Provider):
    scope = Scope.REQUEST
    repository = provide(SqlUserRepository, provides=UserRepository)
    service = provide(UserService)
