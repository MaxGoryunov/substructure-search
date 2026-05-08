# Substructure Search

Substructure search service for chemical compounds.

The current implementation provides:

- an RDKit-powered core function that searches molecule SMILES strings for a
  requested substructure;
- a FastAPI application with in-memory molecule CRUD endpoints;
- a synchronous search endpoint over stored molecules.

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run lint checks:

```bash
flake8 app tests
```

Run the API locally:

```bash
uvicorn app.main:app --reload
```

Run the API with Docker Compose:

```bash
docker compose up --build
```

The API will be available through nginx at `http://127.0.0.1`, with interactive
docs at `http://127.0.0.1/docs`.

Verify load balancing:

```bash
curl http://127.0.0.1/server
```

Repeated requests should alternate between `web-1` and `web-2`.
