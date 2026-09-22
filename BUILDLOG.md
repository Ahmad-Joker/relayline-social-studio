# Build log

## 2026-09-22 — Repository foundation and design

- Feature: initialized the empty repository with submission skeletons and a one-page reliability design.
- Codex involvement: Codex inspected the supplied brief and authored the foundation and design documents.
- Design choices: database-backed polling/leases instead of in-memory timers; stable per-post idempotency keys; webhook-only final delivery state; AES-GCM token sealing; deterministic template captions.
- Failure encountered: the initial local recursive search timed out after 60 seconds and found no fake-platform files. The attachment directory contains only the brief. No fake server was fabricated.
- Tests executed: toolchain availability only; application code does not exist yet.
- Remaining limitations: all implementation, migrations, tests, UI, containers, integration evidence, and acceptance probes remain.

## 2026-09-22 — Content and reliability backend

- Feature: added the initial Alembic schema, exact-size image variants, reusable caption composition, encrypted platform credentials, publisher adapters, a redacting fake-platform client boundary, durable database leasing, bounded retry/rate-limit behavior, crash recovery, and signed/replay-safe delivery webhooks.
- Codex involvement: Codex implemented the backend and deterministic tests from the supplied capstone brief.
- Design choices: PostgreSQL row leases with `FOR UPDATE SKIP LOCKED`; SQLite only for deterministic local unit tests; one stable SHA-256 key per campaign/platform; final state remains webhook-only.
- Failure encountered: two timed-out pip invocations overlapped and locked a Pydantic file on Windows. The stale installer processes completed/terminated, then a single install completed. No tests were hidden or removed.
- Tests executed: `python -m pytest -q` — 17 passed in 17.85s. `alembic upgrade head` against a clean SQLite database also completed and is covered by the test suite.
- Remaining limitations: the React UI, Docker images/Compose, PostgreSQL execution, and real supplied-fake-server probes remain. The fake server is still missing from supplied materials.

## 2026-09-22 — Campaign console and browser integration

- Feature: added the React/Vite dashboard, campaign list, create flow, image upload, scheduling controls, campaign detail, platform previews, retry metadata, and manual publish action.
- Codex involvement: Codex designed and implemented the editorial operations-console interface, then exercised it with an in-app browser against the live FastAPI/SQLite demo.
- Design choices: same-origin `/api` and `/media` development proxies avoid host-name CORS/media mismatches; the UI exposes safe operational state but no credentials or secret material.
- Failures encountered: browser verification found a `localhost`/`127.0.0.1` CORS mismatch, broken absolute media URLs, long-caption horizontal overflow, and a naive/aware SQLite datetime comparison in manual publish. Each root cause was fixed and rechecked. One validation command ran `npm` from the backend directory; it failed as expected, and the build was immediately rerun from `frontend` successfully.
- Tests executed: backend `18 passed in 19.80s`; Vite production build completed with 32 modules. Browser-created campaign `8cf8f520-5906-418a-9a68-c799d7de0c36` rendered both real variants at natural dimensions 1080×1080 and 1600×900. Repeated manual publish left the same two logical social-post rows.
- Remaining limitations: Docker/PostgreSQL and supplied-fake-server integration probes remain.
