from fastapi_canon import Feature

from backend.features.auth.feature import feature as auth
from backend.features.bodyweight.feature import feature as bodyweight
from backend.features.exercises.feature import feature as exercises
from backend.features.plans.feature import feature as plans
from backend.features.training_sessions.feature import feature as training_sessions
from backend.features.users.feature import feature as users
from backend.platform.database.di import DatabaseProvider

FEATURES = (
    Feature(name="database", providers=[DatabaseProvider]),
    auth,
    users,
    exercises,
    plans,
    training_sessions,
    bodyweight,
)
