from pydantic import ConfigDict, EmailStr, Field, SecretStr, field_validator

from backend.platform.api.schema import Schema


class CredentialsRequest(Schema):
    model_config = ConfigDict(str_strip_whitespace=False, hide_input_in_errors=True)

    email: EmailStr = Field(max_length=254)
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().casefold() if isinstance(value, str) else value
