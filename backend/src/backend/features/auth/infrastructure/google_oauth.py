"""Adapted from Maximus' GoogleOAuthClient: server-side code exchange and identity port.

TrainingOS additionally binds the authorization code with PKCE and validates the OIDC nonce.
"""

import base64
import hashlib
import hmac
import time
from urllib.parse import urlencode

import httpx
import jwt
from pydantic import BaseModel, Field

from backend.features.auth.domain import ExternalIdentity, IdentityProvider
from backend.settings import AppSettings
from backend.shared import AuthenticationRequired, ProviderUnavailable


class GoogleTokenResponse(BaseModel):
    id_token: str = Field(min_length=1)


class GoogleClaims(BaseModel):
    sub: str = Field(min_length=1, max_length=255)
    nonce: str
    azp: str | None = None


class GoogleOAuthClient(IdentityProvider):
    def __init__(self, settings: AppSettings, http_client: httpx.AsyncClient) -> None:
        self._settings, self._http = settings, http_client
        self._keys: jwt.PyJWKSet | None = None
        self._keys_until = 0.0

    def _check_configured(self) -> None:
        if (
            not self._settings.google_client_id
            or not self._settings.google_client_secret.get_secret_value()
        ):
            raise ProviderUnavailable

    def authorize_url(self, *, state: str, verifier: str, nonce: str) -> str:
        self._check_configured()
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(
            {
                "client_id": self._settings.google_client_id,
                "redirect_uri": self._settings.google_redirect_uri,
                "response_type": "code",
                "scope": "openid",
                "state": state,
                "nonce": nonce,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        )

    async def _signing_keys(self, *, refresh: bool = False) -> jwt.PyJWKSet:
        if refresh or self._keys is None or time.monotonic() >= self._keys_until:
            response = await self._http.get("https://www.googleapis.com/oauth2/v3/certs")
            response.raise_for_status()
            self._keys = jwt.PyJWKSet.from_dict(response.json())
            self._keys_until = time.monotonic() + 3600
        return self._keys

    async def exchange(self, *, code: str, verifier: str, nonce: str) -> ExternalIdentity:
        self._check_configured()
        try:
            response = await self._http.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": self._settings.google_client_id,
                    "client_secret": self._settings.google_client_secret.get_secret_value(),
                    "redirect_uri": self._settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                    "code_verifier": verifier,
                },
            )
            response.raise_for_status()
            token = GoogleTokenResponse.model_validate(response.json()).id_token
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
                raise AuthenticationRequired
            keys = await self._signing_keys()
            try:
                key = keys[header["kid"]]
            except KeyError:
                keys = await self._signing_keys(refresh=True)
                key = keys[header["kid"]]
            payload = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                audience=self._settings.google_client_id,
                issuer=["https://accounts.google.com", "accounts.google.com"],
                options={"require": ["iss", "aud", "exp", "iat", "sub", "nonce"]},
            )
            claims = GoogleClaims.model_validate(payload)
            if not hmac.compare_digest(claims.nonce, nonce) or (
                claims.azp is not None and claims.azp != self._settings.google_client_id
            ):
                raise AuthenticationRequired
            return ExternalIdentity(issuer="https://accounts.google.com", subject=claims.sub)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500 or exc.response.status_code == 429:
                raise ProviderUnavailable from exc
            raise AuthenticationRequired from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailable from exc
        except (jwt.PyJWTError, ValueError, KeyError, TypeError) as exc:
            raise AuthenticationRequired from exc
