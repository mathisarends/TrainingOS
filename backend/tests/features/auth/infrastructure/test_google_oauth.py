import json
import time
from urllib.parse import parse_qs, urlparse

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import SecretStr

from backend.features.auth.infrastructure.google_oauth import GoogleOAuthClient
from backend.settings import AppSettings
from backend.shared import AuthenticationRequired

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def signing_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def google_transport(
    signing_key: rsa.RSAPrivateKey, *, overrides: dict | None = None, wrong_key: bool = False
) -> httpx.MockTransport:
    now = int(time.time())
    claims = {
        "iss": "https://accounts.google.com",
        "aud": "client-id",
        "sub": "google-subject",
        "exp": now + 300,
        "iat": now,
        "nonce": "expected-nonce",
    } | (overrides or {})
    token_key = (
        rsa.generate_private_key(public_exponent=65537, key_size=2048) if wrong_key else signing_key
    )
    token = jwt.encode(claims, token_key, algorithm="RS256", headers={"kid": "key-1"})
    public_key = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(signing_key.public_key())) | {
        "kid": "key-1",
        "use": "sig",
        "alg": "RS256",
    }

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            body = parse_qs(request.content.decode())
            assert body["code_verifier"] == ["verifier"]
            assert body["redirect_uri"] == ["http://localhost:8000/api/v1/auth/google/callback"]
            return httpx.Response(200, json={"id_token": token})
        assert request.url.path == "/oauth2/v3/certs"
        return httpx.Response(200, json={"keys": [public_key]})

    return httpx.MockTransport(handle)


async def test_google_exchange_validates_signature_and_pkce(signing_key: rsa.RSAPrivateKey) -> None:
    settings = AppSettings(
        google_client_id="client-id", google_client_secret=SecretStr("client-secret")
    )
    async with httpx.AsyncClient(transport=google_transport(signing_key)) as http_client:
        provider = GoogleOAuthClient(settings, http_client)
        url = provider.authorize_url(state="state", verifier="verifier", nonce="expected-nonce")
        query = parse_qs(urlparse(url).query)
        assert query["code_challenge_method"] == ["S256"]
        assert query["scope"] == ["openid"]
        identity = await provider.exchange(code="code", verifier="verifier", nonce="expected-nonce")
    assert identity.subject == "google-subject"


@pytest.mark.parametrize(
    "overrides,wrong_key",
    [
        ({"iss": "https://attacker.example"}, False),
        ({"aud": "different-client"}, False),
        ({"nonce": "wrong-nonce"}, False),
        ({"exp": 1}, False),
        ({"azp": "different-client"}, False),
        ({}, True),
    ],
    ids=["issuer", "audience", "nonce", "expired", "authorized-party", "signature"],
)
async def test_invalid_google_claims_are_not_trusted(
    signing_key: rsa.RSAPrivateKey, overrides: dict, wrong_key: bool
) -> None:
    settings = AppSettings(
        google_client_id="client-id", google_client_secret=SecretStr("client-secret")
    )
    async with httpx.AsyncClient(
        transport=google_transport(signing_key, overrides=overrides, wrong_key=wrong_key)
    ) as http_client:
        provider = GoogleOAuthClient(settings, http_client)
        with pytest.raises(AuthenticationRequired):
            await provider.exchange(code="code", verifier="verifier", nonce="expected-nonce")
