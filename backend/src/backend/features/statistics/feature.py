from fastapi_canon import Feature

from .infrastructure.di import StatisticsProvider
from .presentation.router import router

feature = Feature(name="statistics", providers=[StatisticsProvider], routers=[router])
