from urllib.parse import urlencode

from dishka import Provider, Scope, provide

from backend.features.auth.domain import ExternalIdentity, IdentityProvider
from backend.shared import AuthenticationRequired


class FakeGoogle(IdentityProvider):
    """Only the nondeterministic Google boundary is scripted; auth/SQL/transactions are real."""

    def authorize_url(self, *, state: str, verifier: str, nonce: str) -> str:
        return "https://accounts.google.test/authorize?" + urlencode({"state": state})

    async def exchange(self, *, code: str, verifier: str, nonce: str) -> ExternalIdentity:
        if code == "invalid":
            raise AuthenticationRequired
        return ExternalIdentity(issuer="https://accounts.google.com", subject=code)


class GoogleTestProvider(Provider):
    @provide(scope=Scope.APP, override=True)
    def google(self) -> IdentityProvider:
        return FakeGoogle()
