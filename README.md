# TrainingOS

Backend for strength training plans, set-by-set logging and RPE-based progression.
Built with **fastapi-canon 0.7.0**, FastAPI, Dishka, SQLModel, PostgreSQL and Alembic.
The repository follows the feature/layer structure of Maximus Trading.

## Start locally

Copy `.env.example` to `.env`, enter your Google OAuth web-client credentials,
then run:

```console
docker compose up --build
```

The database becomes healthy first; a dedicated migration container applies Alembic
before the API starts. API: `http://localhost:8000`; interactive contracts:
`http://localhost:8000/docs`; OpenAPI: `http://localhost:8000/openapi.json`.
`/health` is a public liveness check.

For local Python development (Python 3.13 or 3.14, uv):

```console
uv sync --locked --all-packages --all-groups
docker compose up -d database
uv run --locked --package backend trainingos-migrate
uv run --locked --package backend trainingos-api
```

## Google sign-in

Register this exact redirect URI on the Google OAuth web client:
`http://localhost:8000/api/v1/auth/google/callback`.
Open `GET /api/v1/auth/google/login` in the browser. The callback returns the
athlete and sets the HTTP-only application session cookie. There is no password
registration or development authentication bypass.

The auth layout, identity port, server-side callback and cookie helper are adapted
from Maximus. TrainingOS uses PKCE, a browser-bound single-use state and verified
OIDC ID tokens. Its single athlete role uses revocable opaque server sessions;
Maximus' password/admin/approval flows and access/refresh JWT pair are unnecessary
here. Only a SHA-256 digest of each application session token is stored. Signing
in for the first time atomically creates an athlete and the standard catalog.

Cookie-authenticated writes must send an `Origin` from `TRAININGOS_ALLOWED_ORIGINS`;
browser clients must use `credentials: "include"`. Programmatic callers may send
the same opaque session token as `Authorization: Bearer <token>`. Tokens are never
returned in JSON. Logout and account deletion revoke access immediately.

Set `TRAININGOS_ENVIRONMENT=production`, secure cookies, HTTPS callback and explicit
HTTPS origins in deployment. Production startup validates these settings. Supply
database and Google credentials through the deployment environment. The bundled
Compose database credentials and localhost port bindings are for development.
The API command disables access logs because callback query strings carry codes;
configure any reverse proxy to omit OAuth query strings as well.

## API workflow

All business resources are under `/api/v1`, authenticated and athlete-owned.

1. Read `/exercises`; create custom exercises as needed.
2. Create `/plans` with training days (weekday: Monday `0` through Sunday `6`).
3. Add stable exercise slots to `/plans/{plan_id}/days/{day_id}/slots`.
4. Set `/plans/{plan_id}/slots/{slot_id}/weeks/{week}` prescriptions; copy a week
   forward or request `/progression/preview`, then `/progression/apply` with the
   preview's `base_revision` as `expected_revision`.
5. Activate a plan through `/plans/{plan_id}/status`; `/plans/next-training` returns
   the running session or earliest unfinished training day.
6. Start `/sessions`; read slot `/guidance`; explicitly record `/sets`.
7. Adjust `/sessions/{session_id}/timer` or finish the session. Sets and times can
   be corrected afterwards. Statistics and records are derived again on reads.
8. Read `/statistics`, `/statistics/comparison`, `/bodyweight` and `/athlete/export`.

Plan duplication generates new day/slot IDs and copies no sessions. Sharing creates
an immutable template snapshot; another athlete imports it with their own exercise,
day and slot IDs. The share token can be revoked without affecting imported copies.

Input `weight` and output weights/tonnage use the athlete's selected unit. Input
`effort` / `target_effort` use their selected RPE or RIR scale. Responses also expose
canonical RPE. Decimal values serialize as JSON strings. Stored weights are kg;
switching preferences never rewrites historical set values.

The backend persists absolute timer deadlines and returns `server_now`. Wake locks,
OS/background timer notifications and audible signals belong to a future frontend.

## Verification and design

```console
uv run --locked --package backend python scripts/check.py all
```

See [test concept and commands](docs/testing.md), [architecture and decisions](docs/architecture.md)
and the [original specification](docs/specification.txt). SQLite tests run without
Docker; the PostgreSQL lane exercises actual row locks, migrations and concurrent
requests. CI runs both lanes, Python 3.13/3.14, and a production container build.
