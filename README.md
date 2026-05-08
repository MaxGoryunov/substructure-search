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

Run the API locally:

```bash
uvicorn app.main:app --reload
```
