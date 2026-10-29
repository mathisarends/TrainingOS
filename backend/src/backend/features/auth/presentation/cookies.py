from fastapi import Request, Response

from backend.settings import AppSettings
from backend.shared import Forbidden


class AuthCookies:
    """Maximus' HTTP-only cookie boundary, scoped to TrainingOS."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    @property
    def session_name(self) -> str:
        return (
            "__Host-trainingos_session" if self._settings.secure_cookies else "trainingos_session"
        )

    def token(self, request: Request) -> str:
        authorization = request.headers.get("authorization", "")
        if authorization:
            scheme, _, token = authorization.partition(" ")
            return token if scheme.lower() == "bearer" else ""
        return request.cookies.get(self.session_name, "")

    def verify_origin(self, request: Request, *, allow_bearer: bool = True) -> None:
        if request.method not in ("GET", "HEAD", "OPTIONS") and not (
            allow_bearer and request.headers.get("authorization")
        ):
            if request.headers.get("origin") not in self._settings.allowed_origins:
                raise Forbidden

    def set_session(self, response: Response, token: str) -> None:
        response.set_cookie(
            self.session_name,
            token,
            max_age=self._settings.session_days * 86400,
            httponly=True,
            secure=self._settings.secure_cookies,
            samesite="lax",
            path="/",
        )
        response.headers["Cache-Control"] = "no-store"

    def clear_session(self, response: Response) -> None:
        response.delete_cookie(
            self.session_name,
            path="/",
            secure=self._settings.secure_cookies,
            httponly=True,
            samesite="lax",
        )
        response.headers["Cache-Control"] = "no-store"

    def set_oauth_state(self, response: Response, state: str) -> None:
        response.set_cookie(
            "trainingos_oauth_state",
            state,
            max_age=600,
            httponly=True,
            secure=self._settings.secure_cookies,
            samesite="lax",
            path="/api/v1/auth/google",
        )
        response.headers["Cache-Control"] = "no-store"

    def oauth_state(self, request: Request) -> str:
        return request.cookies.get("trainingos_oauth_state", "")

    def clear_oauth_state(self, response: Response) -> None:
        response.delete_cookie(
            "trainingos_oauth_state",
            path="/api/v1/auth/google",
            secure=self._settings.secure_cookies,
            httponly=True,
            samesite="lax",
        )
