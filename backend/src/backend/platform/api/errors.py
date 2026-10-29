from fastapi_canon import Error, ErrorRegistry

from backend.shared import (
    AuthenticationRequired,
    Conflict,
    Forbidden,
    InvalidInput,
    NotFound,
    ProviderUnavailable,
    RateLimited,
)

authentication_required = Error(
    AuthenticationRequired,
    status=401,
    code="authentication_required",
    title="Authentication required",
    detail="Sign in to continue.",
    headers={"WWW-Authenticate": "Bearer"},
    openapi_headers={"WWW-Authenticate": {"schema": {"type": "string"}}},
)
not_found = Error(
    NotFound,
    status=404,
    code="not_found",
    title="Resource not found",
    detail="The requested resource does not exist.",
)
conflict = Error(
    Conflict, status=409, code="state_conflict", title="State conflict", detail=lambda exc: str(exc)
)
invalid_input = Error(
    InvalidInput,
    status=422,
    code="invalid_input",
    title="Invalid input",
    detail=lambda exc: str(exc),
)
forbidden = Error(
    Forbidden,
    status=403,
    code="forbidden",
    title="Request forbidden",
    detail="The request origin could not be verified.",
)
provider_unavailable = Error(
    ProviderUnavailable,
    status=503,
    code="identity_provider_unavailable",
    title="Identity provider unavailable",
    detail="Google sign-in is temporarily unavailable or not configured.",
)
rate_limited = Error(
    RateLimited,
    status=429,
    code="rate_limited",
    title="Too many attempts",
    detail="Too many sign-in attempts. Please wait five minutes and try again.",
    headers={"Retry-After": "300"},
    openapi_headers={"Retry-After": {"schema": {"type": "string"}}},
)
errors = ErrorRegistry(
    name="trainingos",
    errors=[
        authentication_required,
        not_found,
        conflict,
        invalid_input,
        forbidden,
        provider_unavailable,
        rate_limited,
    ],
)
