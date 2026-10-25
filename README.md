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
user and sets the HTTP-only application session cookie. There is no password
registration or development authentication bypass.

The auth layout, identity port, server-side callback and cookie helper are adapted
from Maximus. TrainingOS uses PKCE, a browser-bound single-use state and verified
OIDC ID tokens. Its single user role uses revocable opaque server sessions;
Maximus' password/admin/approval flows and access/refresh JWT pair are unnecessary
here. Only a SHA-256 digest of each application session token is stored. Signing
in for the first time atomically creates an user and the standard catalog.

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

All business resources are under `/api/v1`, authenticated and user-owned.

1. Read `/exercises`; create custom exercises as needed.
2. Create `/plans` with training days (weekday: Monday `0` through Sunday `6`).
3. Add stable exercise slots to `/plans/{plan_id}/days/{day_id}/slots`.
4. Set `/plans/{plan_id}/slots/{slot_id}/weeks/{week}` prescriptions; copy a week
   forward or request `/progression/preview`, then `/progression/apply` with the
   preview's `base_revision` as `expected_revision`.
5. Activate a plan through `/plans/{plan_id}/status`; `/plans/next-training` returns
   the running training session or earliest unfinished training day.
6. Start `/training-sessions`; read slot `/guidance`; explicitly record `/sets`.
7. Adjust `/training-sessions/{training_session_id}/timer` or finish the training
   session. Sets and times can be corrected afterwards; e1RM and record detection
   use the corrected values.
8. Read `/bodyweight` and `/users/me/export`; manage preferences through
   `/users/me/preferences` and delete the account through `/users/me`.

Plan duplication generates new day/slot IDs and copies no training sessions. Sharing creates
an immutable template snapshot; another user imports it with their own exercise,
day and slot IDs. The share token can be revoked without affecting imported copies.

Input `weight` and output weights use the user's selected unit. Input
`effort` / `target_effort` use their selected RPE or RIR scale. Responses also expose
canonical RPE. Decimal values serialize as JSON strings. Stored weights are kg;
switching preferences never rewrites historical set values.

The backend persists absolute timer deadlines and returns `server_now`. Wake locks,
OS/background timer notifications and audible signals belong to a future frontend.

## Architecture

`backend/src/backend` follows the Maximus feature layout:

```text
backend/
  src/backend/
    app.py / composition.py       # Canon composition and feature registration
    features/<feature>/
      domain/                    # Framework-free entities, rules and ABC ports
      application/               # Constructor-injected use cases
      infrastructure/            # SQL and Google adapters, Dishka providers
      presentation/              # HTTP schemas, mappers and routers
      feature.py                 # Feature assembly
    platform/                    # Shared API and database mechanisms
  tests/features/<feature>/<layer>/
  tests/platform/
```

Dependencies point inward: presentation calls application, application uses domain
ports, and infrastructure implements those ports. Package facades do not assemble
the application. Canon owns Problem Details and OpenAPI; route operation IDs and
success statuses are explicit.

PostgreSQL stores relational ownership and indexes. Nested plan and training-session contents
are JSON aggregate snapshots with explicit codecs and Decimal weights. Every owned
query includes the user ID. Request-scoped owner row locks serialize aggregate
mutations; database constraints additionally enforce one active plan, one running
training session and one training session per training day/week.

Repositories flush without committing. The function-scoped Dishka transaction commits
before a successful response is sent and rolls back on failure. Alembic owns schema
changes and ships inside the installed package; runtime never calls `create_all`.
Deleting a user cascades their data. Deleting a plan preserves recorded training sessions.
Exercises referenced by captured training sessions are archived rather than removed.

Week 1 spans seven days beginning at the plan's start date; weekday offsets wrap
within it. Recommendations use the latest preceding performance of the same slot
with matching prescribed reps. e1RM rounds upward; backoff rounds half up to the
nearest increment. Deload reduces sets by one, with a minimum of one. Training
session corrections update the history used for subsequent recommendations and
personal-record detection.

The original requirements are preserved in [SPECIFICATION.txt](SPECIFICATION.txt).
The current scope uses users and explicit training sessions; the separate statistics
and plan-comparison feature has been removed.

The database migration from `0001` to `0002` renames account ownership to `user_id`
and updates stored plan/template payloads without replacing IDs or training values.
Account export format 2 uses `user` and `training_sessions`; set feedback returns
`training_session`. Login sessions remain authentication infrastructure.

## Test concept

Tests mirror the production feature and layer under `backend/tests`. The path names
the subject; pytest markers identify the boundary:

| Marker | Boundary and guarantees |
| --- | --- |
| `unit` | Domain rules, calculations, timers and configuration; Google adapter tests use scripted HTTP and real RSA/JWT verification. |
| `integration` | Actual Canon composition, Dishka providers, services, repositories, Alembic migrations and transactions; only the external Google provider is replaced. |
| `contract` | HTTP/OpenAPI, unique operation IDs, named Problem Details and rejected-write behavior. |
| `postgres` | Concurrent plan activation, session starts and set recording against real PostgreSQL and separate request transactions. |

`conftest.py` owns databases, application lifespans and HTTP clients; shared setup is
in `support.py`, provider doubles in `fakes.py`. Assertions observe committed data
through another request or connection. Tests verify rollback after flushed writes,
user isolation, account deletion, immutable session history, independent template
copies and recalculated personal records. Domain timers use explicit timestamps;
concurrency checks use bounded waits without arbitrary sleeps.

The default database is a fresh SQLite file per test, created through the production
migration. PostgreSQL-only cases explicitly skip in this lane. SQLite does not
establish PostgreSQL locking guarantees.

```console
uv run --locked --package backend python scripts/check.py all
uv run --locked --package backend pytest -m unit
uv run --locked --package backend pytest -m "integration and not postgres"
uv run --locked --package backend pytest -m contract
```

For the PostgreSQL lane, start a disposable test database:

```console
docker run --rm -d --name trainingos-test-db -e POSTGRES_USER=trainingos -e POSTGRES_PASSWORD=trainingos_test -e POSTGRES_DB=trainingos_test -p 127.0.0.1:55439:5432 postgres:18-alpine
docker exec trainingos-test-db pg_isready -U trainingos -d trainingos_test
```

Once PostgreSQL is ready, set its URL and run the suite (PowerShell):

```powershell
$env:TRAININGOS_TEST_POSTGRES_URL = 'postgresql+asyncpg://trainingos:trainingos_test@localhost:55439/trainingos_test'
uv run --locked --package backend pytest -q
docker stop trainingos-test-db
```

The role needs `CREATEDB`, and the source database name must contain `test`. Each
test creates and drops a uniquely named database. CI requires the PostgreSQL lane
and configures the portable lane for Windows/Linux and Python 3.13/3.14, plus a
production container build.

Verification on 2026-10-25: **62 passed against PostgreSQL 18**; SQLite:
**59 passed, 3 PostgreSQL-only cases skipped**. This includes migration of populated
legacy accounts, plans, templates and training sessions, followed by downgrade and
another upgrade. Ruff, strict mypy and package builds passed. The Linux package
checks the renamed APIs and packaged migration; the initial container migration/HTTP
smoke checks also passed.
Python 3.13 and the hosted CI matrix were configured rather than locally executed.
Live Google consent needs the owner's OAuth credentials. Wake locks and background
timer signals require a future browser/OS integration suite.
