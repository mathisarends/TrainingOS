from dishka import Provider, Scope, provide

from backend.features.exercises.application import ExerciseService
from backend.features.exercises.domain import ExerciseRepository
from backend.features.exercises.infrastructure.repository import SqlExerciseRepository


class ExerciseProvider(Provider):
    scope = Scope.REQUEST
    repository = provide(SqlExerciseRepository, provides=ExerciseRepository)
    service = provide(ExerciseService)
