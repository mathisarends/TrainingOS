from fastapi_canon import Feature

from .infrastructure.di import PlanProvider
from .presentation.router import router, templates_router

feature = Feature(name="plans", providers=[PlanProvider], routers=[router, templates_router])
