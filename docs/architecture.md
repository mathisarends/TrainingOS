# Architecture

`backend/src/backend` mirrors the Maximus layout: `app.py` is the composition root,
`composition.py` lists feature contributions, `main.py` owns the server entrypoint,
`platform` owns transport/database mechanics, and `features` own business behavior.
Each feature contains domain, application, infrastructure and presentation only
where needed. Public domain/application names are exported through package facades.

```text
presentation -> application -> domain
infrastructure -------------> domain
feature.py / composition root -> outer-layer wiring
```

Domain entities are ordinary classes with named transitions and read-only identity.
Frozen dataclasses represent prescriptions, slots, snapshots and result projections.
Owned repository/provider contracts are ABCs; adapters inherit them explicitly.
Pydantic is restricted to settings, HTTP contracts and persistence/provider codecs.

## Persistence and transactions

PostgreSQL is the production store. SQLModel describes nine tables; Alembic's frozen
initial revision owns schema creation. Runtime startup never calls `create_all`.
The migrations ship inside the installed Python package and container.

Athletes, external identities, login sessions, exercises, plans, templates,
training sessions and bodyweight entries have relational ownership and indexes.
Plans and training sessions store their nested contents as JSON aggregate snapshots.
These are deliberately aggregate-owned, not individually queried SQL child records.
Explicit persistence codecs restore fully materialized domain values; no lazy
relationships escape the SQL scope. Weights remain Decimal strings inside snapshots.

Every protected resource query includes the authenticated athlete ID. Authentication
locks the athlete row for the request, serializing that athlete's aggregate changes
while allowing different athletes to proceed independently. Partial unique indexes
enforce at most one active plan and one running session per athlete. A unique key
prevents duplicate day/week sessions. The login identity unique key and savepoint
handle concurrent first sign-in without a duplicate athlete/catalog.

Repositories flush but never commit. A function-scoped FastAPI dependency closes
the Dishka request scope before success is sent. The SQL provider interprets Dishka's
exception value: success commits, failure/cancellation rolls back. PostgreSQL tests
verify concurrent requests; integration tests inspect writes through new requests.
The owner lock also covers reads for a simple consistent v1 boundary. If read load
requires it later, separate read-only scopes while retaining locks on mutations.

Deleting a plan removes its future planning aggregate. Sessions retain the former
plan/day/slot identities and snapshots, so statistics can still filter that plan ID.
Deleting an athlete cascades all owned records, templates and authentication state.
OAuth attempts are transient pre-account records and expire after ten minutes.
An exercise referenced by any captured session is archived even before its first
set, so subsequent recording/correction cannot create a dangling exercise reference.

## Training semantics

- An exercise slot's UUID is its history key; list position never identifies it.
- A session captures exercise name/category, prescribed reps/RPE and rest interval.
  Reordering/removing slots or changing the catalog leaves this snapshot intact.
- Catalog changes update future plan metadata. Current main-exercise selection
  determines which exercises participate in records; archived main exercises remain.
- All recorded sets are work sets. No warmup/background draft values are persisted.
- e1RM uses Epley plus `10 - RPE`, rounded upward in the selected unit. Backoff uses
  that rounded maximum and rounds half up to the nearest configured increment.
- Recommendations use the most recent preceding session of the same slot with
  matching **prescribed** reps. The best e1RM among its sets predicts the current
  target. Actual deviations in reps are included in e1RM. No match means null.
- Progression regenerates all weeks after week 1, including manually edited values.
  Main exercises cap at RPE 9, others at 10. Optional final deload uses RPE 6/7 and
  one fewer set, floored at one because zero sets is not a valid prescription.
- A preview performs no writes. Applying checks the original revision and recomputes
  the same deterministic rules with the requested increment/deload options.
- Plan week 1 is the seven-day interval starting at `start_date`. Weekday offsets
  wrap within that interval. Next training is the earliest incomplete day in order;
  future days can still be selected manually. At most one day/week session is logged.
- Duplicate/imported plans have fresh slot IDs and deliberately start new slot history.
- Statistics are derived from recorded sets, including a running session, on every
  read. Corrections therefore cannot leave stale cached totals or personal records.
  Weekly buckets use plan week numbers; activity dates use the athlete's IANA timezone.
- The timer's UTC deadline is persisted with the session. Responses include server
  time for clock skew; the frontend can restore a countdown after reload.

## API contracts

Canon owns error rendering and OpenAPI Problem Details. Route operation IDs and
success statuses are explicit. Request schemas forbid unknown fields, reject
non-finite numbers and constrain sizes. Named mappers separate domain and wire shapes.
Google credentials, session digests and provider payloads never appear in public data.
Training exports include identity references and share snapshots but exclude secrets.
