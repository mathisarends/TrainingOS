from fastapi_canon import Feature

from .infrastructure.di import AthleteProvider
from .presentation.router import router

feature = Feature(name="athletes", providers=[AthleteProvider], routers=[router])
