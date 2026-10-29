# TrainingOS

Strength training plans, set-by-set logging and RPE-based progression, with a
responsive Lit/TypeScript frontend and a feature-oriented Python backend.
Built with **fastapi-canon 0.7.0**, FastAPI, Dishka, SQLModel, PostgreSQL and Alembic.
The repository follows the feature/layer structure of Maximus Trading.

## Start locally

Copy `.env.example` to `.env`, then run:

```console
docker compose up --build
```

The database becomes healthy first; a dedicated migration container applies Alembic
before the API starts. Frontend: `http://localhost:5173`; API: `http://localhost:8000`; interactive contracts:
`http://localhost:8000/docs`; OpenAPI: `http://localhost:8000/openapi.json`.
`/health` is a public liveness check. Create an account at `/register`, then sign in
at `/login` with email and password. Google credentials are optional and only
needed for the retained Google endpoints.

For local Python development (Python 3.13 or 3.14, uv):

```console
uv sync --locked --all-packages --all-groups
docker compose up -d database
uv run --locked --package backend trainingos-migrate
uv run --locked --package backend trainingos-api
```

In a second terminal, with Node.js 24 and npm:

```console
cd frontend
npm ci
npm run dev
```

The frontend proxies `/api` to `http://127.0.0.1:8000`, including cookie-authenticated
requests. Keep port 5173 available, or update `TRAININGOS_FRONTEND_URL` and
`TRAININGOS_ALLOWED_ORIGINS` to match the browser origin when choosing another port.
Vite fails on a port conflict instead of silently changing the origin.

## Frontend

The frontend follows the eight supplied desktop/mobile design references, preserved
unchanged in [`frontend/references`](frontend/references/index.html). The reference
gallery identifies Home, Training, Logs and Account at both viewport sizes. System
notifications and the decorative phone frame in those images are capture artifacts;
they are not application UI.

The visual contract lives in [`frontend/src/tokens.css`](frontend/src/tokens.css):
charcoal backgrounds (`#202020`), subtly raised surfaces, fine neutral borders,
light text, green completion indicators, a system sans-serif with monospaced progress
labels, shared spacing, rounded panels and a floating four-item navigation. The
header and main content share a centered content column; Account has a narrower
column. Mobile layouts use full-width stacked cards with safe-area-aware navigation.

Home cards show the real completed training days in each plan week; an active
plan highlights its current calendar week. The training preview uses a desktop
table and labeled exercise cards on mobile, with day/week controls above the
content and a floating mobile start action. Logs uses desktop calendar entries and
mobile completion dots plus a monthly session list. Account groups its menu into
outlined panels below the activity year, with a 30-day completion count and legend.
Dashboard history is paginated completely so plan progress and activity counts do
not stop at the first API page. Recorded history remains the source of completion.

The remaining screens infer the same design language: outlined category tables,
rounded plan/set editors, neutral charts and record cards, grouped settings and
data forms, and dark dialogs. This includes authentication, plan creation,
progression, sharing, exercise editing and recorded training sessions.
The creation dialog collects title and block length, then training days and start
date; plan cover images are not part of the interface.

Pages and flows:

- `/login` and `/register`: real email/password sign-in and registration in a
  separate layout, following the Maximus Trading auth shell and form styles. The
  desktop layout places a 408px form next to decorative training progression
  artwork; mobile uses only the form. Authentication colors, type and sizing are
  shared tokens. `/getting-started` remains a compatible login alias; anonymous
  application visits open `/login`. Google is retained in the backend.

- `/`: plan cards; create, open, edit and delete plans while retaining training history.
  A full-width first-plan panel provides a direct creation action for new users.
- `/plans`, `/plans/new` and `/plans/:id`: plan settings, named weekdays, exercise slots,
  reordering/removal, rest times and per-week prescriptions. Duplicate, activate,
  archive, copy forward, share/import/revoke templates, and preview/apply progression
  with the backend's revision check.
  Creation uses a two-step dialog: title/block length in
  General, then weekday selection and start date in Calendar. Day names can be
  customized without leaving the calendar step; moving back preserves the form.
- `/training` and `/training/:id`: day/week navigation, start/resume, explicit set
  recording, previous performance, backend e1RM/backoff feedback, skipping exercises,
  completion, set correction/deletion and training-time correction.
- `/logs`: monthly calendar, month navigation, list view and reopening recorded sessions.
- `/profile`: account menu and a recent-training activity calendar.
- `/profile/exercises`: inline name editing and the original category tables with
  rest, set, repetition and effort defaults. Search/filter and create/edit/remove
  remain available. Failed inline changes retain their drafts for explicit retry.
  Category defaults are labeled compact controls, with two columns on mobile.
- `/profile/best-performance`: main-exercise best values and history using the
  backend-returned e1RM values; no separate statistics or plan-comparison feature.
- `/profile/settings`: kg/lb, RPE/RIR, rounding step and timezone.
- `/profile/data`: JSON export and explicitly confirmed account deletion.

Select fields share `training-select`, a dark popover/listbox with keyboard navigation,
type-ahead, Escape/outside dismissal and a quiet selected state. Native selects remain
the form-data and validation source; choosing an option emits a single change event.
Inline name edits use an inset focus border. Settings and data links have descriptive
subtitles; their destinations use consistent grouped surfaces.

Email/password registration, login, cookie session restoration and logout use the
backend. The existing Google OAuth endpoints remain available.
All production calculations and persistence remain there. Failed writes preserve
form input and never appear saved. Mutations and failed reads are not retried
automatically; ambiguous network writes require checking the server state before
resubmitting. Authentication and training data are not stored in local storage.
`/?demo=1` explicitly selects isolated in-memory sample data for all pages. Reloading
resets this preview; it never substitutes for unavailable real data. Old hash links
are migrated to the corresponding pathname, including recorded-session links.

### Lit Canon conventions and generated API

The app uses `createApp`, `defineFeature`, `definePage` and `provide` from
[lit-canon](https://github.com/mathisarends/lit-canon). Each feature owns `feature.ts`
with explicit, lazy page registration. Composition supplies a single TanStack
`QueryClient`, the server-state store, navigation and the transport through Lit
context. Cache invalidation uses generated key factories; logout clears the cache.
Structural sharing is disabled to preserve response receipt timestamps for timers.

The not-yet-published `lit-canon-api`, `lit-canon-fetch` and
`lit-canon-composition` packages are vendored from the local upstream snapshot
`d1838b16ac06d70fefc540400a96fe752281b9e9` under `frontend/vendor/lit-canon` and
installed through relative npm `file:` dependencies. Their source, compiled runtime
and MIT notices are included. Only packaging metadata was adapted (`dist` is called
`lib`, development dependencies and upstream build scripts are omitted); runtime
and generator source are unchanged. No sibling checkout or published Canon package
is required to install or build this repository.

`frontend/openapi.json` comes from the actual backend composition. The upstream
Canon generator owns `frontend/src/api/generated`: typed resource clients, DTOs,
query keys/options, mutation factories and Problem Details unions. Application DTOs
are aliases of those contracts. `src/api/request.ts` is the single injectable
request boundary; production uses `lit-canon-fetch`, while preview/tests supply an
isolated transport. UI code calls generated operations rather than handwritten URLs.

Regenerate after backend contract changes:

```console
uv run --locked --package backend python scripts/export_openapi.py
cd frontend
npm run api:generate
```

On Windows, stop Vite before generation: its watcher can prevent the generator's
atomic directory replacement. The read-only `api:check` works while Vite is running.
Checks:

```console
uv run --locked --package backend python scripts/export_openapi.py --check
cd frontend
npm ci
npm run api:check
npm test
npm run build
npm run format:check
```

Tests mirror subjects under `frontend/tests`. They cover request credentials,
decimal serialization, errors/cancellation, explicit set entry, duplicate submission,
late guidance, server-deadline timers, plan creation and revision-checked progression,
calendar navigation and failed catalog writes. CI checks both the exported
OpenAPI contract and regenerated client. The latest visual checkpoints are saved under
[`frontend/screenshots/reference-redesign`](frontend/screenshots/reference-redesign/index.html).
Earlier checkpoints remain in `frontend/screenshots` for comparison.

Local verification on 2026-10-29: 35 frontend tests and 85 backend tests passed
(4 PostgreSQL-only cases skipped), along with TypeScript/Vite, Prettier, Ruff, mypy
and both API drift checks. A clean `npm ci` was verified. Application routes were checked
at 320, 390 and 1600 pixels for visible errors and horizontal overflow; desktop
and mobile screenshots include the forms and dialogs. Login and registration
were additionally checked at 320, 390 and 1440 pixels. Browser checks also covered
day/week navigation, training start, explicit set recording and the rest timer,
plus real local registration, cookie restoration, logout and subsequent login.
Google consent and locked-screen device signals were not tested against a real
account/device.

The latest [UI polish checkpoints](frontend/screenshots/ui-polish/index.html) cover
the empty home page, compact defaults, dropdowns, inline focus, account, settings and
data screens. Browser checks include 320/390px mobile and 1440px desktop layouts,
popover behavior inside a dialog, and a real preference save verified after reloading.
Bodyweight removal is checked by upgrading populated legacy data and inspecting it
from a separate database scope; recorded training weights remain unchanged.

The frontend container builds from this checkout, including the vendored packages,
then serves through nginx and proxies `/api` to the API container. Its SPA fallback
supports direct page URLs. OAuth query strings are excluded from access logs.
The manifest supplies standalone metadata; there is no service worker or offline
write queue. Start locally with Node.js 24 and `npm ci && npm run dev` in `frontend`.

For a real phone, use one reachable hostname for frontend and OAuth callback,
register the exact callback with Google, and configure that frontend origin in
`TRAININGOS_FRONTEND_URL` and `TRAININGOS_ALLOWED_ORIGINS`. HTTPS enables secure
cookies and Screen Wake Lock. Compose binds to localhost by default. Mobile browsers
can suspend background pages, so locked-screen audio/vibration is browser-dependent;
the server deadline remains correct after returning or reloading.

## Sign-in and registration

`POST /api/v1/auth/register` creates an account and standard exercise catalog in
one transaction, then establishes the same opaque HTTP-only cookie session used
by Google. `POST /api/v1/auth/login` authenticates an existing account. Both accept
`email` and `password`. Registration requires 15–128 characters; passwords retain
whitespace, while email identifiers are validated and normalized case-insensitively.
Replacing the browser session revokes its previous token. Logout revokes access;
account deletion cascades local credentials. The data export includes the login
email and never includes password hashes or session secrets.

Passwords use Argon2id (19 MiB, two iterations, one lane), following the
[OWASP password storage guidance](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).
Hashing runs off the event loop with bounded concurrency; unknown users perform a
dummy verification and receive the same 401 response as incorrect passwords.
Login and registration require an explicitly allowed request Origin, including
requests carrying an Authorization header. The bounded in-process throttle permits
10 attempts per email and 30 per client address in five minutes, then returns 429
and Retry-After. Multi-worker deployments should add a shared reverse-proxy limit;
this process-local limiter does not claim distributed enforcement.

Email is a sign-in identifier, not a verified identity claim. Email verification
and password recovery are not implemented. Existing Google identities are not
automatically linked to local accounts by email. Google OAuth remains an optional,
independent sign-in method in the backend; its buttons are omitted from the UI.

### Optional Google sign-in

Register this exact redirect URI on the Google OAuth web client:
`http://localhost:8000/api/v1/auth/google/callback`.
Open `GET /api/v1/auth/google/login` in the browser. The callback returns the
user and sets the HTTP-only application session cookie. Browser navigations accepting
HTML receive a 303 redirect to `TRAININGOS_FRONTEND_URL`; JSON API clients retain the
200 user response. The redirect target must be an explicitly allowed origin.
Email/password sign-in does not need a Google client. There is no development
authentication bypass.

The auth layout, identity port, server-side callback and cookie helper are adapted
from Maximus. TrainingOS uses PKCE, a browser-bound single-use state and verified
OIDC ID tokens. Its single user role uses revocable opaque server sessions;
Maximus' admin/approval flows and access/refresh JWT pair are unnecessary here.
Only a SHA-256 digest of each application session token is stored. Signing
in for the first time atomically creates a user and the standard catalog.

Cookie-authenticated writes must send an `Origin` from `TRAININGOS_ALLOWED_ORIGINS`;
browser clients must use `credentials: "include"`. Programmatic callers may send
the same opaque session token as `Authorization: Bearer <token>`. Tokens are never
returned in JSON. Logout and account deletion revoke access immediately.

Set `TRAININGOS_ENVIRONMENT=production`, secure cookies, HTTPS callback and explicit
HTTPS origins in deployment. Production startup validates these settings. Supply
database credentials through the deployment environment and Google credentials
only when enabling its OAuth endpoints. The bundled
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
8. Read `/users/me/export`; manage preferences through
   `/users/me/preferences` and delete the account through `/users/me`.

Plan duplication generates new day/slot IDs and copies no training sessions. Sharing creates
an immutable template snapshot; another user imports it with their own exercise,
day and slot IDs. The share token can be revoked without affecting imported copies.

Input `weight` and output weights use the user's selected unit. Input
`effort` / `target_effort` use their selected RPE or RIR scale. Responses also expose
canonical RPE. Decimal values serialize as JSON strings. Stored weights are kg;
switching preferences never rewrites historical set values.

The backend persists absolute timer deadlines and returns `server_now`. The frontend
anchors these to response receipt time and a monotonic clock, including cached
snapshots after navigation. Native OS background notifications remain outside the
browser implementation.

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
Account exports use `user` and `training_sessions`; set feedback returns
`training_session`. Login sessions remain authentication infrastructure.

Migration `0003` adds owned exercise-category defaults. Missing overrides resolve
to the original TrainingSystems values; changing defaults never rewrites existing
plan prescriptions or captured training sessions. Adding a new slot uses its
category defaults for every week, with an optional explicit rest override. Effort
is stored as RPE and mapped to the user's RPE/RIR preference at the API boundary.
Account exports include the resolved category defaults; account deletion cascades
stored overrides. Apply the normal migration command before starting the new API.

Migration `0004` adds local password credentials without changing existing Google
identities or user IDs. Registration rollback, duplicate normalized emails,
password whitespace, session replacement/revocation, origin checks, throttling,
secret-free validation/export, and account deletion are covered through the real
composition and separate request/database scopes. Concurrent registration is
covered in the PostgreSQL test lane.

Migration `0005` completely removes bodyweight tracking: it drops stored measurements
and removes target-weight preferences. Downgrading recreates an empty table; deleted
measurements cannot be recovered by a downgrade. The API and frontend no longer expose
these fields or routes. Export format 3 omits bodyweight and target weight. Recorded
training-session weights and plan prescriptions are preserved and verified after
the migration from a separate database scope.

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
concurrency checks use bounded waits without arbitrary sleeps. The SQLite adapter
uses explicit BEGIN statements so savepoint release cannot escape request rollback,
following [SQLAlchemy transaction control](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#enabling-non-legacy-sqlite-transactional-modes-with-the-sqlite3-or-aiosqlite-driver).

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
