import pytest
from pydantic import SecretStr, ValidationError

from backend.settings import AppSettings

pytestmark = pytest.mark.unit


def test_production_rejects_insecure_auth_configuration() -> None:
    with pytest.raises(ValidationError, match="secure cookies"):
        AppSettings(environment="production", secure_cookies=False)


def test_production_accepts_https_and_explicit_origins() -> None:
    settings = AppSettings(
        environment="production",
        secure_cookies=True,
        google_redirect_uri="https://training.example/api/v1/auth/google/callback",
        google_client_id="client-id",
        google_client_secret=SecretStr("client-secret"),
        allowed_origins=["https://training.example"],
        frontend_url="https://training.example",
    )
    assert settings.secure_cookies
