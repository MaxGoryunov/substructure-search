# Open PR And Issue Analysis

Source: `Project.pdf`, `docs/requirements.md`, open GitHub issues, and open GitHub pull requests in `origin`.

## Current Open Scope

| Issue | PR | Component | Assessment |
|---|---|---|---|
| #1 | #2 | RDKit search core | Satisfies the issue scope: project structure, RDKit parsing/matching, invalid substructure handling, skipped invalid molecules, and focused tests are present. |
| #3 | #4 | FastAPI CRUD with RAM storage | Satisfies the issue scope: CRUD endpoints, health endpoint, Pydantic schemas, in-memory repository, synchronous stored-molecule search, and API tests are present. |
| #5 | #6 | Docker Compose application setup | Satisfies the issue scope: `Dockerfile`, `.dockerignore`, Compose web service, Uvicorn startup, RDKit dependency installation path, and port `8000` exposure are present. |
| #7 | #8 | nginx load balancing | Satisfies the issue scope: two web services, nginx reverse proxy, upstream configuration, port `80`, `/server`, and verification documentation are present. |
| #9 | #10 | CI and flake8 | Required a fix before merge: editable install failed because setuptools discovered both `app` and `nginx` as top-level packages. Added explicit package discovery for `app*`. |

## Merge Readiness

```mermaid
flowchart TD
    A["Project.pdf requirements"] --> B["Issue #1 / PR #2: RDKit core"]
    B --> C["Issue #3 / PR #4: FastAPI + RAM storage"]
    C --> D["Issue #5 / PR #6: Docker Compose"]
    D --> E["Issue #7 / PR #8: nginx balancing"]
    E --> F["Issue #9 / PR #10: CI + flake8"]
    F --> G{"Local verification"}
    G -->|install failed| H["Fix pyproject package discovery"]
    H --> I["Run pytest and flake8"]
    I --> J["Merge ready if checks pass"]
```

## Remaining Project.pdf Requirements After The First Five PRs

The PDF-derived requirements still not covered by the currently open issue/PR set are:

| Component | Required Work |
|---|---|
| PostgreSQL + SQLAlchemy | Replace RAM storage with persistent database storage, add a `postgres` Compose service, use `.env` credentials, and keep molecules across restarts. |
| Logging + iterator listing | Add standard `logging` for CRUD, search, validation errors, cache, and task lifecycle events; keep listing iterator-friendly and enforce `limit`. |
| Redis search cache | Add Redis, cache search results with TTL, handle cache hit/miss, and prevent stale results after molecule changes. |
| Celery async search | Add Celery worker, use Redis broker/backend, start search tasks through one endpoint, and read task status/result through another endpoint. |
| Optional upload | Add file upload for molecule imports if time allows. |

## Recommended Next Branches

```mermaid
gitGraph
    commit id: "main-after-pr10"
    branch "codex/11-postgres-sqlalchemy"
    checkout "codex/11-postgres-sqlalchemy"
    commit id: "postgres"
    checkout main
    merge "codex/11-postgres-sqlalchemy"
    branch "codex/12-logging-iterator"
    checkout "codex/12-logging-iterator"
    commit id: "logging-limit"
    checkout main
    merge "codex/12-logging-iterator"
    branch "codex/13-redis-cache"
    checkout "codex/13-redis-cache"
    commit id: "redis-cache"
    checkout main
    merge "codex/13-redis-cache"
    branch "codex/14-celery-search"
    checkout "codex/14-celery-search"
    commit id: "celery"
```
