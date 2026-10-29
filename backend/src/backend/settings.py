from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRAININGOS_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://trainingos:trainingos@localhost:5432/trainingos"
    environment: Literal["local", "production"] = "local"
    secure_cookies: bool = False
    allowed_origins: list[str] = ["http://localhost:5173"]
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    frontend_url: str = "http://localhost:5173"
    session_days: int = Field(default=30, ge=1, le=90)
    oauth_timeout_seconds: float = Field(default=10, gt=0, le=60)
    host: str = "127.0.0.1"
    port: int = 8000

    @model_validator(mode="after")
    def production_settings(self) -> Self:
        if self.frontend_url not in self.allowed_origins:
            raise ValueError("Frontend URL must be an explicitly allowed origin")
        if self.environment == "production":
            if not self.secure_cookies or not self.google_redirect_uri.startswith("https://"):
                raise ValueError("Production requires secure cookies and an HTTPS OAuth callback")
            if not self.google_client_id or not self.google_client_secret.get_secret_value():
                raise ValueError("Production requires Google OAuth credentials")
            if not self.allowed_origins or any(
                not origin.startswith("https://") for origin in self.allowed_origins
            ):
                raise ValueError("Production requires explicit HTTPS origins")
        return self
