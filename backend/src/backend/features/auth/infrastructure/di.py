from collections.abc import AsyncIterator

import httpx
from dishka import Provider, Scope, provide

from backend.features.auth.application import AuthService, GoogleAuthService
from backend.features.auth.domain import AuthRepository, IdentityProvider
from backend.features.auth.domain.credentials import (
    CredentialRepository,
    CredentialThrottle,
    PasswordHasher,
)
from backend.features.auth.infrastructure.credentials import SqlCredentialRepository
from backend.features.auth.infrastructure.google_oauth import GoogleOAuthClient
from backend.features.auth.infrastructure.passwords import ArgonPasswords
from backend.features.auth.infrastructure.repository import SqlAuthRepository
from backend.features.auth.infrastructure.throttle import InMemoryCredentialThrottle
from backend.features.auth.presentation.cookies import AuthCookies
from backend.features.exercises.domain import ExerciseRepository
from backend.features.users.domain import UserRepository
from backend.settings import AppSettings


class AuthProvider(Provider):
    scope = Scope.APP
    cookies = provide(AuthCookies)
    google_service = provide(GoogleAuthService, scope=Scope.REQUEST)
    identity_provider = provide(GoogleOAuthClient, provides=IdentityProvider)
    repository = provide(SqlAuthRepository, provides=AuthRepository, scope=Scope.REQUEST)
    credentials = provide(
        SqlCredentialRepository, provides=CredentialRepository, scope=Scope.REQUEST
    )
    passwords = provide(ArgonPasswords, provides=PasswordHasher)
    throttle = provide(InMemoryCredentialThrottle, provides=CredentialThrottle)

    @provide
    async def http_client(self, settings: AppSettings) -> AsyncIterator[httpx.AsyncClient]:
        async with httpx.AsyncClient(
            timeout=settings.oauth_timeout_seconds, follow_redirects=False
        ) as client:
            yield client

    @provide(scope=Scope.REQUEST)
    def auth_service(
        self,
        auth_repository: AuthRepository,
        user_repository: UserRepository,
        exercise_repository: ExerciseRepository,
        settings: AppSettings,
        credentials: CredentialRepository,
        passwords: PasswordHasher,
        throttle: CredentialThrottle,
    ) -> AuthService:
        return AuthService(
            auth_repository,
            user_repository,
            exercise_repository,
            settings.session_days,
            credentials,
            passwords,
            throttle,
        )
