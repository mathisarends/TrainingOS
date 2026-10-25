from dishka.integrations.fastapi import FromDishka
from fastapi import Response

from backend.features.athletes.application import AthleteService
from backend.features.athletes.domain import Preferences
from backend.features.auth.presentation import CurrentAthlete
from backend.features.auth.presentation.cookies import AuthCookies
from backend.platform.api.router import protected_router

from .export import AccountExportResponse, to_export_response
from .mapper import to_response
from .schemas import AthleteResponse, PreferencesRequest

router = protected_router(prefix="/athlete", tag="athletes")


@router.put(
    "/preferences",
    operation_id="configure_athlete",
    status_code=200,
    response_model=AthleteResponse,
)
async def configure_athlete(
    body: PreferencesRequest, athlete: CurrentAthlete, athlete_service: FromDishka[AthleteService]
) -> AthleteResponse:
    unit_preferences = Preferences(unit=body.unit)
    preferences = Preferences(
        unit=body.unit,
        rounding_step=body.rounding_step,
        effort_scale=body.effort_scale,
        target_weight_kg=unit_preferences.to_kg(body.target_weight)
        if body.target_weight is not None
        else None,
        timezone=body.timezone,
    )
    updated = await athlete_service.configure(athlete_id=athlete.id, preferences=preferences)
    return to_response(updated)


@router.get(
    "/export",
    operation_id="export_athlete_data",
    status_code=200,
    response_model=AccountExportResponse,
)
async def export_athlete(
    athlete: CurrentAthlete, response: Response, athlete_service: FromDishka[AthleteService]
) -> AccountExportResponse:
    export = await athlete_service.export(athlete_id=athlete.id)
    response.headers["Content-Disposition"] = 'attachment; filename="trainingos-export.json"'
    response.headers["Cache-Control"] = "no-store"
    return to_export_response(export)


@router.delete("", operation_id="delete_athlete_account", status_code=204, response_model=None)
async def delete_athlete(
    athlete: CurrentAthlete,
    athlete_service: FromDishka[AthleteService],
    auth_cookies: FromDishka[AuthCookies],
) -> Response:
    await athlete_service.delete(athlete_id=athlete.id)
    response = Response(status_code=204)
    auth_cookies.clear_session(response)
    return response
