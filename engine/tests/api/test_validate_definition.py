"""Validate definition endpoint tests -- TDD RED phase."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


@pytest.fixture
def valid_definition(project_root: Path) -> dict:
    defs_dir = project_root / "definitions"
    path = next(defs_dir.glob("*.json"))
    return json.loads(path.read_text())


class TestValidateDefinitionEndpoint:
    def test_valid_definition_returns_200(
        self, client: TestClient, valid_definition: dict
    ) -> None:
        resp = client.post("/api/v1/validate-definition", json=valid_definition)
        assert resp.status_code == 200

    def test_valid_definition_returns_valid_true(
        self, client: TestClient, valid_definition: dict
    ) -> None:
        resp = client.post("/api/v1/validate-definition", json=valid_definition)
        data = resp.json()
        assert data["valid"] is True
        assert data["errors"] == []

    def test_invalid_definition_returns_valid_false(
        self, client: TestClient
    ) -> None:
        invalid = {"program_id": "bad", "version": "1.0.0"}  # missing required fields
        resp = client.post("/api/v1/validate-definition", json=invalid)
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0

    def test_empty_body_returns_valid_false(self, client: TestClient) -> None:
        resp = client.post("/api/v1/validate-definition", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False

    def test_errors_are_strings(self, client: TestClient) -> None:
        resp = client.post("/api/v1/validate-definition", json={})
        data = resp.json()
        assert all(isinstance(e, str) for e in data["errors"])

    def test_non_json_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/validate-definition",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422
