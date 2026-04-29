"""API endpoint tests -- written FIRST (TDD RED phase)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_200(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Exercise Library
# ---------------------------------------------------------------------------

class TestExerciseLibraryEndpoint:
    def test_get_library(self, client: TestClient) -> None:
        resp = client.get("/api/v1/exercise-library")
        assert resp.status_code == 200
        data = resp.json()
        assert "exercises" in data
        assert len(data["exercises"]) > 50

    def test_library_has_version(self, client: TestClient) -> None:
        resp = client.get("/api/v1/exercise-library")
        data = resp.json()
        assert "version" in data


# ---------------------------------------------------------------------------
# Program Definitions
# ---------------------------------------------------------------------------

class TestDefinitionsEndpoint:
    def test_list_definitions(self, client: TestClient) -> None:
        resp = client.get("/api/v1/program-definitions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_get_definition_by_id(self, client: TestClient) -> None:
        resp = client.get(
            "/api/v1/program-definitions/strength_ul_4w_v1"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["program_id"] == "strength_ul_4w_v1"

    def test_get_definition_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/v1/program-definitions/nonexistent")
        assert resp.status_code == 404

    def test_get_conditioning_definition(
        self, client: TestClient
    ) -> None:
        resp = client.get(
            "/api/v1/program-definitions/conditioning_4w_v1"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["program_id"] == "conditioning_4w_v1"


# ---------------------------------------------------------------------------
# Plan Generation
# ---------------------------------------------------------------------------

class TestGenerateEndpoint:
    def test_generate_strength_plan(self, client: TestClient) -> None:
        request_body = {
            "program_id": "strength_ul_4w_v1",
            "program_version": "1.0.0",
            "weeks": 4,
            "days_per_week": 4,
            "athlete": {
                "level": "intermediate",
                "time_budget_minutes": 90,
                "equipment": [
                    "barbell", "rack", "bench",
                    "dumbbells", "cable", "machine", "pullup_bar",
                ],
                "e1rm": {
                    "squat": 160.0,
                    "bench": 115.0,
                    "deadlift": 190.0,
                    "ohp": 70.0,
                },
            },
            "rules": {
                "rounding_profile": "plate_2p5kg",
                "volume_metric": "hard_sets_weighted",
                "allow_optional_ohp": True,
                "hard_set_rule": "RIR_LE_4",
                "main_method": "HYBRID",
                "accessory_rir_target": 2,
            },
        }
        resp = client.post("/api/v1/generate", json=request_body)
        assert resp.status_code == 200
        data = resp.json()
        assert "weeks" in data
        assert len(data["weeks"]) == 4
        assert data["program_id"] == "strength_ul_4w_v1"

    def test_generate_conditioning_plan(
        self, client: TestClient
    ) -> None:
        request_body = {
            "program_id": "conditioning_4w_v1",
            "program_version": "1.0.0",
            "weeks": 4,
            "days_per_week": 4,
            "athlete": {
                "level": "intermediate",
                "time_budget_minutes": 60,
                "modality": "run",
                "equipment": [],
            },
            "conditioning": {
                "method": "HR_ZONES",
                "hr_zone_formula": "KARVONEN_HRR",
                "hr_max": 190,
                "hr_rest": 55,
            },
        }
        resp = client.post("/api/v1/generate", json=request_body)
        assert resp.status_code == 200
        data = resp.json()
        assert "weeks" in data
        assert data["program_id"] == "conditioning_4w_v1"

    def test_generate_invalid_request(
        self, client: TestClient
    ) -> None:
        resp = client.post("/api/v1/generate", json={})
        assert resp.status_code == 422

    def test_generate_unknown_program(
        self, client: TestClient
    ) -> None:
        request_body = {
            "program_id": "nonexistent_program",
            "program_version": "1.0.0",
            "weeks": 4,
            "days_per_week": 4,
            "athlete": {
                "level": "intermediate",
                "time_budget_minutes": 60,
                "equipment": [],
            },
        }
        resp = client.post("/api/v1/generate", json=request_body)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Error Responses
# ---------------------------------------------------------------------------

class TestErrorResponses:
    def test_404_returns_json(self, client: TestClient) -> None:
        resp = client.get("/api/v1/nonexistent-route")
        assert resp.status_code == 404

    def test_422_returns_detail(self, client: TestClient) -> None:
        resp = client.post("/api/v1/generate", json={})
        assert resp.status_code == 422
        data = resp.json()
        assert "detail" in data
