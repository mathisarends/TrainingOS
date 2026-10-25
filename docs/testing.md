# Test concept

Tests mirror their production subject, rather than separating all tests into global
technical buckets. A path identifies the subject; markers identify the boundary.

| Production subject | Mirrored tests | Boundary / regression |
| --- | --- | --- |
| `features/training/domain` | `features/training/domain` | Epley rounding, inverse backoff, lb and RIR rules |
| `features/plans/domain` | `features/plans/domain` | Progression caps, deload, stable slot identity |
| `features/sessions/domain` | `features/sessions/domain` | Absolute deadlines, ordered timestamps, completion |
| `features/auth/infrastructure` | `features/auth/infrastructure` | Real Google adapter with scripted HTTP; RSA signature and claim rejection |
| `features/auth/presentation` | `features/auth/presentation` | Real login/session SQL; state binding, replay, origin checks, logout |
| `features/athletes/presentation` | `features/athletes/presentation` | Ownership, export, complete account cascade |
| `features/exercises/presentation` | `features/exercises/presentation` | Archive historical exercises; future plan vs captured session metadata |
| `features/plans/presentation` | `features/plans/presentation` | Preview/apply, active-plan transitions, independent templates |
| `features/sessions/presentation` | `features/sessions/presentation` | Recording, correction, timer reload, slot reorder and rep matching |
| `features/statistics/presentation` | `features/statistics/presentation` | Multi-plan volume and corrected record history |
| `features/bodyweight/presentation` | `features/bodyweight/presentation` | One weigh-in per date and target weight |
| `platform/api` | `platform/api` | Named Problem Details, unique operations, rejected-write invariants |
| `platform/database` | `platform/database` | Migration drift/round trip, request rollback, PostgreSQL concurrency |
| `settings.py` | `settings/test_settings.py` | Production auth configuration |

Framework-free tests use the smallest useful domain boundary. HTTP integration tests
run the actual Canon composition, Dishka providers, services, SQL repositories,
migrations and commit/rollback scopes. Only Google is replaced at its declared port;
the separate Google adapter suite uses real JWT verification and a scripted HTTP
transport. There is no test-only authentication route or mocked application response.

`conftest.py` owns the database, app lifespan and HTTP clients. Shared setup mechanics
live in `support.py`, external provider doubles in `fakes.py`. Expected behavior stays
in the scenario. Tests do not import another test or conftest module. All created
clients, engines and application containers have explicit teardown. Database writes
are asserted through a subsequent request or independent connection, never just the
object returned by the producing repository. Timer unit tests use explicit times.
Concurrent tests have bounded waits and no arbitrary sleeps.

## Commands

```console
uv sync --locked --all-packages --all-groups
uv run --locked --package backend python scripts/check.py all
uv run --locked --package backend pytest -m unit
uv run --locked --package backend pytest -m "integration and not postgres"
uv run --locked --package backend pytest -m contract
```

The default integration database is a fresh SQLite file per test, created through
the production Alembic migration. PostgreSQL-only tests explicitly skip in this lane.
This establishes HTTP/persistence behavior, not PostgreSQL locking guarantees.

For the PostgreSQL lane, start a disposable database (the name must contain `test`):

```console
docker run --rm -d --name trainingos-test-db -e POSTGRES_USER=trainingos -e POSTGRES_PASSWORD=trainingos_test -e POSTGRES_DB=trainingos_test -p 127.0.0.1:55439:5432 postgres:18-alpine
```

Set `TRAININGOS_TEST_POSTGRES_URL` to
`postgresql+asyncpg://trainingos:trainingos_test@localhost:55439/trainingos_test` in your
shell, then run the suite. PowerShell example:

```powershell
$env:TRAININGOS_TEST_POSTGRES_URL = 'postgresql+asyncpg://trainingos:trainingos_test@localhost:55439/trainingos_test'
uv run --locked --package backend pytest -q
docker stop trainingos-test-db
```

The role needs `CREATEDB`. Every test creates and drops a uniquely named database,
so source data and unrelated databases are never reset. The PostgreSQL lane must
actually run the `postgres` marker: active-plan races, competing session starts and
simultaneous set recording cannot be established by SQLite. CI makes this lane
mandatory and runs the portable lane on Windows/Linux and Python 3.13/3.14.

## Requirements and limits

- N-01/02/03/05/06: auth, account/ownership and cascade tests.
- N-04, R-01/02/08: calculations, lb/RIR workflow and preference tests.
- F-01–04: seeded categories, custom exercise deletion and historical archiving.
- F-10–19: plan domain/API, progression preview, duplication, next day and templates.
- F-20–24/26/27, R-05/06/07: session workflow, correction and slot-history tests.
- F-30/31/33: explicit-time domain tests and reload/adjust/skip API workflow.
- F-40–42: no-match guidance, prior matching reps, reordered slots and disable switch.
- F-50–53: main/accessory cap and deload domain cases, stale preview/API apply.
- F-60–65/70/71: plan comparison, live record notice and corrected record history.
- F-80/81: dated bodyweight replacement, target and deletion.

F-25 and F-32 require browser/OS integration (wake lock and background notification).
They cannot be verified by backend tests. A live Google-consent round trip requires
the owner's configured OAuth client; automated tests verify the real adapter's
cryptographic boundary and the application's complete callback/session workflow.
The requirement mapping describes scenario coverage, not a claim of exhaustive
coverage for every input combination. No blanket coverage percentage substitutes
for these boundaries.

## Initial verification — 2026-10-25

- Windows / Python 3.14: **61 passed** against PostgreSQL 18, including all concurrency cases.
- Portable SQLite lane: **58 passed, 3 PostgreSQL-only tests skipped**.
- Ruff lint/format and strict mypy: passed.
- Wheel and source distribution: built; packaged Alembic revision/template verified.
- Linux production image: built and imported from its installed package as UID 10001.
- Container migration against PostgreSQL: passed. Live HTTP smoke: health/OpenAPI 200,
  protected resource 401 and unconfigured Google login 503, with a healthy container.

Python 3.13 and the GitHub-hosted matrix are configured in CI, not claimed as locally
executed. Live Google consent requires the owner's OAuth credentials and was not run.
