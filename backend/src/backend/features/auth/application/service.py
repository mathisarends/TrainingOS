import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from backend.features.auth.domain import (
    AuthRepository,
    ExternalIdentity,
    LoginSession,
)
from backend.features.auth.domain.credentials import (
    CredentialRepository,
    CredentialThrottle,
    PasswordCredential,
    PasswordHasher,
)
from backend.features.exercises.domain import STANDARD_CATALOG, Exercise, ExerciseRepository
from backend.features.users.domain import User, UserRepository
from backend.shared import AuthenticationRequired, Conflict, InvalidInput


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass(frozen=True)
class SignedIn:
    user: User
    token: str


class AuthService:
    def __init__(
        self,
        auth_repository: AuthRepository,
        user_repository: UserRepository,
        exercise_repository: ExerciseRepository,
        session_days: int,
        credentials: CredentialRepository,
        passwords: PasswordHasher,
        throttle: CredentialThrottle,
    ) -> None:
        self._auth, self._users, self._exercises = (
            auth_repository,
            user_repository,
            exercise_repository,
        )
        self._session_days = session_days
        self._credentials, self._passwords, self._throttle = credentials, passwords, throttle

    async def password_register(self, *, email: str, password: str, client_key: str) -> SignedIn:
        email = email.strip().casefold()
        await self._throttle.check(email_key=token_hash(email), client_key=token_hash(client_key))
        if not 15 <= len(password) <= 128:
            raise InvalidInput("Use a password with 15 to 128 characters.")
        encoded = await self._passwords.hash(password=password)
        user_id = uuid4()
        created = await self._credentials.register(
            credential=PasswordCredential(user_id, email, encoded)
        )
        if not created:
            raise Conflict("Registration could not be completed. Sign in or use another email.")
        user = await self._users.get(user_id=user_id, lock=True)
        if user is None:
            raise AuthenticationRequired
        await self._seed_catalog(user=user)
        return await self._sign_in(user=user)

    async def password_login(self, *, email: str, password: str, client_key: str) -> SignedIn:
        email = email.strip().casefold()
        await self._throttle.check(email_key=token_hash(email), client_key=token_hash(client_key))
        credential = await self._credentials.find(email=email)
        if (
            not await self._passwords.verify(
                password=password, encoded=credential.password_hash if credential else None
            )
            or credential is None
        ):
            raise AuthenticationRequired
        user = await self._users.get(user_id=credential.user_id, lock=True)
        if user is None:
            raise AuthenticationRequired
        return await self._sign_in(user=user)

    async def _seed_catalog(self, *, user: User) -> None:
        for name, category, main in STANDARD_CATALOG:
            await self._exercises.save(
                exercise=Exercise(user_id=user.id, name=name, category=category, main=main)
            )

    async def _sign_in(self, *, user: User) -> SignedIn:
        token = secrets.token_urlsafe(48)
        await self._auth.save_session(
            login_session=LoginSession(
                token_hash=token_hash(token),
                user_id=user.id,
                expires_at=datetime.now(UTC) + timedelta(days=self._session_days),
            )
        )
        return SignedIn(user=user, token=token)

    async def external_sign_in(self, *, identity: ExternalIdentity) -> SignedIn:
        candidate_id = uuid4()
        user_id = await self._auth.resolve_identity(identity=identity, candidate_id=candidate_id)
        user = await self._users.get(user_id=user_id, lock=True)
        if user is None:
            raise AuthenticationRequired
        if candidate_id == user_id:
            await self._seed_catalog(user=user)
        return await self._sign_in(user=user)

    async def current(self, *, token: str) -> User:
        login_session = await self._auth.get_session(token_hash=token_hash(token))
        if login_session is None or login_session.expires_at <= datetime.now(UTC):
            raise AuthenticationRequired
        # Serialize owner mutations, including active-plan transitions and account deletion.
        user = await self._users.get(user_id=login_session.user_id, lock=True)
        if user is None:
            raise AuthenticationRequired
        login_session = await self._auth.get_session(token_hash=token_hash(token))
        if login_session is None or login_session.expires_at <= datetime.now(UTC):
            raise AuthenticationRequired
        return user

    async def logout(self, *, token: str) -> None:
        await self._auth.revoke(token_hash=token_hash(token))
