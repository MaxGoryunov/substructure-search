# PostgreSQL And SQLAlchemy Component

Source: `Project.pdf`, `docs/requirements.md`, and the current FastAPI/RAM implementation.

## Goal

Replace volatile RAM storage with persistent molecule storage while keeping the existing API contract unchanged.

## Implemented Design

- `DATABASE_URL` enables persistent storage.
- Without `DATABASE_URL`, the app keeps using `InMemoryMoleculeRepository`, which keeps local tests lightweight.
- With `DATABASE_URL`, the app creates a SQLAlchemy engine and uses `SQLAlchemyMoleculeRepository`.
- Docker Compose adds a `db` service based on PostgreSQL and stores credentials in `.env`.
- The `molecules` table stores `identifier` as the primary key and `smiles` as the molecule value.

## Runtime Flow

```mermaid
flowchart TD
    A["FastAPI startup"] --> B{"DATABASE_URL set?"}
    B -->|No| C["InMemoryMoleculeRepository"]
    B -->|Yes| D["SQLAlchemy engine"]
    D --> E["Create molecules table if needed"]
    E --> F["SQLAlchemyMoleculeRepository"]
    C --> G["CRUD and search endpoints"]
    F --> G
    G --> H["RDKit substructure search"]
    F --> I[("PostgreSQL")]
```

## Persistence Verification

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant DB as PostgreSQL

    Client->>API: POST /molecules
    API->>DB: INSERT molecule
    API-->>Client: 201 molecule
    Client->>API: Restart web container
    Client->>API: GET /molecules/{identifier}
    API->>DB: SELECT molecule
    API-->>Client: 200 molecule
```

## Manual Check

1. Copy `.env.example` to `.env`.
2. Run `docker compose up --build`.
3. Create a molecule through `POST /molecules`.
4. Restart `web1` or `web2`.
5. Read the same molecule through `GET /molecules/{identifier}`.
