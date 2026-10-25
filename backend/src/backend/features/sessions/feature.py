from fastapi_canon import Feature

from .infrastructure.di import SessionProvider
from .presentation.router import router

feature = Feature(name="sessions", providers=[SessionProvider], routers=[router])
