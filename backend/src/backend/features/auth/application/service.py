import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from backend.features.athletes.domain import Athlete, AthleteRepository
from backend.features.auth.domain import (
    AuthRepository,
    IdentityProvider,
    LoginAttempt,
    LoginSession,
)
from backend.features.exercises.domain import STANDARD_CATALOG, Exercise, ExerciseRepository
from backend.shared import AuthenticationRequired


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass(frozen=True)
class Authorization:
    url: str
    state: str


@dataclass(frozen=True)
class SignedIn:
    athlete: Athlete
    token: str


class AuthService:
    def __init__(
        self,
        auth_repository: AuthRepository,
        athlete_repository: AthleteRepository,
        exercise_repository: ExerciseRepository,
        identity_provider: IdentityProvider,
        session_days: int,
    ) -> None:
        self._auth, self._athletes, self._exercises = (
            auth_repository,
            athlete_repository,
            exercise_repository,
        )
        self._google, self._session_days = identity_provider, session_days

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
        candidate_id = uuid4()
        athlete_id = await self._auth.resolve_identity(identity=identity, candidate_id=candidate_id)
        athlete = await self._athletes.get(athlete_id=athlete_id, lock=True)
        if athlete is None:
            raise AuthenticationRequired
        if candidate_id == athlete_id:
            for name, category, main in STANDARD_CATALOG:
                exercise = Exercise(athlete_id=athlete_id, name=name, category=category, main=main)
                await self._exercises.save(exercise=exercise)
        token = secrets.token_urlsafe(48)
        login_session = LoginSession(
            token_hash=token_hash(token),
            athlete_id=athlete_id,
            expires_at=datetime.now(UTC) + timedelta(days=self._session_days),
        )
        await self._auth.save_session(login_session=login_session)
        return SignedIn(athlete=athlete, token=token)

    async def current(self, *, token: str) -> Athlete:
        login_session = await self._auth.get_session(token_hash=token_hash(token))
        if login_session is None or login_session.expires_at <= datetime.now(UTC):
            raise AuthenticationRequired
        # Serialize owner mutations, including active-plan transitions and account deletion.
        athlete = await self._athletes.get(athlete_id=login_session.athlete_id, lock=True)
        if athlete is None:
            raise AuthenticationRequired
        login_session = await self._auth.get_session(token_hash=token_hash(token))
        if login_session is None:
            raise AuthenticationRequired
        return athlete

    async def logout(self, *, token: str) -> None:
        await self._auth.revoke(token_hash=token_hash(token))
