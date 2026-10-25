from collections.abc import AsyncIterator

import httpx
from dishka import Provider, Scope, provide

from backend.features.athletes.domain import AthleteRepository
from backend.features.auth.application import AuthService
from backend.features.auth.domain import AuthRepository, IdentityProvider
from backend.features.auth.infrastructure.google_oauth import GoogleOAuthClient
from backend.features.auth.infrastructure.repository import SqlAuthRepository
from backend.features.auth.presentation.cookies import AuthCookies
from backend.features.exercises.domain import ExerciseRepository
from backend.settings import AppSettings


class AuthProvider(Provider):
    scope = Scope.APP
    cookies = provide(AuthCookies)
    identity_provider = provide(GoogleOAuthClient, provides=IdentityProvider)
    repository = provide(SqlAuthRepository, provides=AuthRepository, scope=Scope.REQUEST)

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
        athlete_repository: AthleteRepository,
        exercise_repository: ExerciseRepository,
        identity_provider: IdentityProvider,
        settings: AppSettings,
    ) -> AuthService:
        return AuthService(
            auth_repository,
            athlete_repository,
            exercise_repository,
            identity_provider,
            settings.session_days,
        )
