import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from backend.features.auth.domain import AuthRepository, IdentityProvider, LoginAttempt
from backend.shared import AuthenticationRequired

from .service import AuthService, SignedIn, token_hash


@dataclass(frozen=True)
class Authorization:
    url: str
    state: str


class GoogleAuthService:
    def __init__(
        self,
        auth_repository: AuthRepository,
        identity_provider: IdentityProvider,
        auth_service: AuthService,
    ) -> None:
        self._auth = auth_repository
        self._google = identity_provider
        self._sessions = auth_service

    async def google_authorization(self) -> Authorization:
        state, verifier, nonce = (secrets.token_urlsafe(32) for _ in range(3))
        url = self._google.authorize_url(state=state, verifier=verifier, nonce=nonce)
        attempt = LoginAttempt(
            state_hash=token_hash(state),
            verifier=verifier,
            nonce=nonce,
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
        await self._auth.save_attempt(attempt=attempt)
        return Authorization(url=url, state=state)

    async def google_callback(self, *, code: str, state: str, expected_state: str) -> SignedIn:
        if not state or not expected_state or not hmac.compare_digest(state, expected_state):
            raise AuthenticationRequired
        attempt = await self._auth.consume_attempt(state_hash=token_hash(state))
        if attempt is None or attempt.expires_at <= datetime.now(UTC):
            raise AuthenticationRequired
        identity = await self._google.exchange(
            code=code, verifier=attempt.verifier, nonce=attempt.nonce
        )
        return await self._sessions.external_sign_in(identity=identity)
