from dataclasses import dataclass
from uuid import UUID

from backend.features.auth.domain import AuthRepository, ExternalIdentity
from backend.features.bodyweight.domain import BodyweightRepository, WeighIn
from backend.features.exercises.domain import (
    CategoryDefaults,
    Exercise,
    ExerciseRepository,
    resolve_defaults,
)
from backend.features.plans.domain import Plan, PlanRepository
from backend.features.training_sessions.domain import TrainingSession, TrainingSessionRepository
from backend.features.users.domain import Preferences, User, UserRepository
from backend.shared import NotFound


@dataclass(frozen=True)
class AccountExport:
    user: User
    exercises: list[Exercise]
    plans: list[Plan]
    training_sessions: list[TrainingSession]
    bodyweight: list[WeighIn]
    identities: list[ExternalIdentity]
    shared_templates: list[Plan]
    category_defaults: list[CategoryDefaults]


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        exercise_repository: ExerciseRepository,
        plan_repository: PlanRepository,
        training_session_repository: TrainingSessionRepository,
        bodyweight_repository: BodyweightRepository,
        auth_repository: AuthRepository,
    ) -> None:
        self._users, self._exercises, self._plans = (
            user_repository,
            exercise_repository,
            plan_repository,
        )
        self._training_sessions, self._bodyweight = (
            training_session_repository,
            bodyweight_repository,
        )
        self._auth = auth_repository

    async def configure(self, *, user_id: UUID, preferences: Preferences) -> User:
        user = await self._users.get(user_id=user_id)
        if user is None:
            raise NotFound
        user.configure(preferences)
        await self._users.save(user=user)
        return user

    async def delete(self, *, user_id: UUID) -> None:
        await self._users.delete(user_id=user_id)

    async def export(self, *, user_id: UUID) -> AccountExport:
        user = await self._users.get(user_id=user_id)
        if user is None:
            raise NotFound
        return AccountExport(
            user=user,
            exercises=await self._exercises.list(user_id=user_id),
            plans=await self._plans.list(user_id=user_id),
            training_sessions=await self._training_sessions.list(user_id=user_id),
            bodyweight=await self._bodyweight.list(user_id=user_id),
            identities=await self._auth.identities(user_id=user_id),
            shared_templates=await self._plans.templates(user_id=user_id),
            category_defaults=resolve_defaults(
                await self._exercises.list_defaults(user_id=user_id)
            ),
        )
