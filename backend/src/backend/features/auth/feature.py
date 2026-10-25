from fastapi_canon import Feature

from .infrastructure.di import AuthProvider
from .presentation.router import router

feature = Feature(name="auth", providers=[AuthProvider], routers=[router])
