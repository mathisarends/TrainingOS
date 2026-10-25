# TrainingOS backend

Use the current Canon guides and the architecture in `docs/architecture.md`.
Keep documentation in English. Product terminology follows `docs/specification.txt`.

- Own business code by `backend/src/backend/features/<feature>/<layer>`.
- Domain is framework-free; application depends on nominal domain ports, never adapters.
- Put HTTP schemas/mappers in presentation and SQL/Google adapters in infrastructure.
- Keep feature assembly in `feature.py`, and package facades free of composition side effects.
- Use Canon `Feature`, `Composition`, `CanonRouter` and Problem Details contracts.
- Inject dependencies with Dishka. The function request scope owns commit/rollback.
- Every owned query includes `athlete_id`. Keep owner row locks for aggregate mutations.
- Never mutate recorded session snapshots when editing a plan or exercise catalog.
- Mirror test subjects under `backend/tests/<production path>`; see `docs/testing.md`.
- Verify persistence from another request/session after the producing scope closes.
- Use PostgreSQL for locking/concurrency claims. SQLite does not establish these guarantees.
- Run `uv run --locked --package backend python scripts/check.py all` before finishing.
- Deployments and remote pushes require a user request. Local incremental commits are welcome.
