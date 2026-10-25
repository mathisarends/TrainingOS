from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ExternalIdentity:
    issuer: str
    subject: str


@dataclass(frozen=True)
class LoginAttempt:
    state_hash: str
    verifier: str
    nonce: str
    expires_at: datetime


@dataclass(frozen=True)
class LoginSession:
    token_hash: str
    athlete_id: UUID
    expires_at: datetime
