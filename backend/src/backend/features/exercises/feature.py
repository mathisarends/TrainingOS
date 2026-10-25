from fastapi_canon import Feature

from .infrastructure.di import ExerciseProvider
from .presentation.router import router

feature = Feature(name="exercises", providers=[ExerciseProvider], routers=[router])
