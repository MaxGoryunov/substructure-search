from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app, repository


@pytest.fixture(autouse=True)
def clear_repository() -> Iterator[None]:
    repository.clear()
    yield
    repository.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_server_endpoint_returns_default_server_id(client: TestClient) -> None:
    response = client.get("/server")

    assert response.status_code == 200
    assert response.json() == {"server_id": "local"}


def test_creates_and_reads_molecule(client: TestClient) -> None:
    create_response = client.post(
        "/molecules",
        json={"identifier": "ethanol", "smiles": "CCO"},
    )

    assert create_response.status_code == 201
    assert create_response.json() == {"identifier": "ethanol", "smiles": "CCO"}

    read_response = client.get("/molecules/ethanol")

    assert read_response.status_code == 200
    assert read_response.json() == {"identifier": "ethanol", "smiles": "CCO"}


def test_rejects_duplicate_identifier(client: TestClient) -> None:
    payload = {"identifier": "benzene", "smiles": "c1ccccc1"}

    assert client.post("/molecules", json=payload).status_code == 201
    response = client.post("/molecules", json=payload)

    assert response.status_code == 409


def test_rejects_invalid_molecule_smiles(client: TestClient) -> None:
    response = client.post(
        "/molecules",
        json={"identifier": "bad", "smiles": "not-smiles"},
    )

    assert response.status_code == 422


def test_updates_molecule(client: TestClient) -> None:
    client.post("/molecules", json={"identifier": "sample", "smiles": "CCO"})

    response = client.put("/molecules/sample", json={"smiles": "CCN"})

    assert response.status_code == 200
    assert response.json() == {"identifier": "sample", "smiles": "CCN"}


def test_deletes_molecule(client: TestClient) -> None:
    client.post("/molecules", json={"identifier": "sample", "smiles": "CCO"})

    delete_response = client.delete("/molecules/sample")
    read_response = client.get("/molecules/sample")

    assert delete_response.status_code == 204
    assert read_response.status_code == 404


def test_lists_molecules_with_limit(client: TestClient) -> None:
    client.post("/molecules", json={"identifier": "one", "smiles": "CCO"})
    client.post("/molecules", json={"identifier": "two", "smiles": "CCN"})

    response = client.get("/molecules", params={"limit": 1})

    assert response.status_code == 200
    assert response.json() == [{"identifier": "one", "smiles": "CCO"}]


def test_lists_no_molecules_when_limit_is_zero(client: TestClient) -> None:
    client.post("/molecules", json={"identifier": "one", "smiles": "CCO"})

    response = client.get("/molecules", params={"limit": 0})

    assert response.status_code == 200
    assert response.json() == []


def test_rejects_negative_list_limit(client: TestClient) -> None:
    response = client.get("/molecules", params={"limit": -1})

    assert response.status_code == 422


def test_searches_stored_molecules(client: TestClient) -> None:
    client.post("/molecules", json={"identifier": "ethanol", "smiles": "CCO"})
    client.post("/molecules", json={"identifier": "benzene", "smiles": "c1ccccc1"})
    client.post(
        "/molecules",
        json={"identifier": "aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O"},
    )

    response = client.post("/search", json={"substructure": "c1ccccc1"})

    assert response.status_code == 200
    assert response.json() == {
        "substructure": "c1ccccc1",
        "matches": [
            {"identifier": "benzene", "smiles": "c1ccccc1"},
            {"identifier": "aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O"},
        ],
    }


def test_rejects_invalid_search_substructure(client: TestClient) -> None:
    response = client.post("/search", json={"substructure": "not-smiles"})

    assert response.status_code == 422
