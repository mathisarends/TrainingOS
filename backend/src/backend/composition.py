from fastapi_canon import Feature

from backend.features.athletes.feature import feature as athletes
from backend.features.auth.feature import feature as auth
from backend.features.bodyweight.feature import feature as bodyweight
from backend.features.exercises.feature import feature as exercises
from backend.features.plans.feature import feature as plans
from backend.features.sessions.feature import feature as sessions
from backend.features.statistics.feature import feature as statistics
from backend.platform.database.di import DatabaseProvider

FEATURES = (
    Feature(name="database", providers=[DatabaseProvider]),
    auth,
    athletes,
    exercises,
    plans,
    sessions,
    bodyweight,
    statistics,
)
