from fastapi_canon import Feature

from .infrastructure.di import UserProvider
from .presentation.router import router

feature = Feature(name="users", providers=[UserProvider], routers=[router])
