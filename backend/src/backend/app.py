from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_canon import CanonRouter, Composition, ErrorOptions, Feature

from backend.composition import FEATURES
from backend.platform.api.request_scope import http_request_scope
from backend.platform.api.schema import Schema
from backend.settings import AppSettings


class HealthResponse(Schema):
    status: str = "ok"


def create_app(*extra_features: Feature) -> FastAPI:
    settings = AppSettings()
    application = FastAPI(
        title="TrainingOS API",
        version="0.1.0",
        summary="Plan, record and progressively overload strength training.",
        dependencies=[Depends(http_request_scope, scope="function")],
    )

    @application.get(
        "/health",
        operation_id="get_health",
        status_code=200,
        response_model=HealthResponse,
        tags=["system"],
    )
    async def health() -> HealthResponse:
        return HealthResponse()

    composition = Composition(
        *FEATURES,
        *extra_features,
        router_factory=lambda: CanonRouter(prefix="/api/v1"),
        errors=ErrorOptions(type_base="urn:trainingos:problem"),
    )
    composition.apply(application)
    composition.validate(application)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    return application


app = create_app()
