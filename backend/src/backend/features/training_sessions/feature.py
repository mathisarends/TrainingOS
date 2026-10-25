from fastapi_canon import Feature

from .infrastructure.di import TrainingSessionProvider
from .presentation.router import router

feature = Feature(name="training_sessions", providers=[TrainingSessionProvider], routers=[router])
