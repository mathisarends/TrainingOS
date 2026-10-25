from fastapi_canon import Feature

from .infrastructure.di import BodyweightProvider
from .presentation.router import router

feature = Feature(name="bodyweight", providers=[BodyweightProvider], routers=[router])
