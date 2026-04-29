"""Exercise alternatives endpoint tests -- TDD RED phase."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


class TestExerciseAlternativesEndpoint:
    def test_returns_200_with_valid_exercise(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/exercises/alternatives",
            json={
                "exercise_id": "back_squat",
                "athlete_equipment": ["barbell", "rack"],
            },
        )
        assert resp.status_code == 200

    def test_response_structure(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/exercises/alternatives",
            json={
                "exercise_id": "back_squat",
                "athlete_equipment": ["barbell", "rack"],
            },
        )
        data = resp.json()
        assert data["original_exercise_id"] == "back_squat"
        assert isinstance(data["alternatives"], list)

    def test_swap_group_alternatives_returned(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/exercises/alternatives",
            json={
                "exercise_id": "back_squat",
                "athlete_equipment": ["barbell", "rack"],
            },
        )
        data = resp.json()
        alternatives = data["alternatives"]
        # back_squat is in squat_main group; front_squat, high_bar_squat, low_bar_squat too
        alt_ids = [a["id"] for a in alternatives]
        assert "front_squat" in alt_ids or "high_bar_squat" in alt_ids

    def test_swap_group_alternatives_appear_before_pattern_matches(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/api/v1/exercises/alternatives",
            json={
                "exercise_id": "back_squat",
                "athlete_equipment": ["barbell", "rack", "machine"],
                "limit": 10,
            },
        )
        data = resp.json()
        alternatives = data["alternatives"]
        reasons = [a["match_reason"] for a in alternatives]
        # All swap_group reasons should come before any pattern_match reasons
        if "pattern_match" in reasons:
            first_pattern_idx = reasons.index("pattern_match")
            assert all(r == "swap_group" for r in reasons[:first_pattern_idx])

    def test_returns_404_for_unknown_exercise(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/exercises/alternatives",
            json={
                "exercise_id": "nonexistent_exercise_xyz",
                "athlete_equipment": ["barbell"],
            },
        )
        assert resp.status_code == 404

    def test_exclude_ids_respected(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/exercises/alternatives",
            json={
                "exercise_id": "back_squat",
                "athlete_equipment": ["barbell", "rack"],
                "exclude_ids": ["front_squat", "high_bar_squat"],
            },
        )
        data = resp.json()
        alt_ids = [a["id"] for a in data["alternatives"]]
        assert "front_squat" not in alt_ids
        assert "high_bar_squat" not in alt_ids

    def test_limit_respected(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/exercises/alternatives",
            json={
                "exercise_id": "back_squat",
                "athlete_equipment": ["barbell", "rack", "machine"],
                "limit": 2,
            },
        )
        data = resp.json()
        assert len(data["alternatives"]) <= 2

    def test_equipment_filter_applied(self, client: TestClient) -> None:
        # Without barbell/rack equipment, squat_main alternatives are not available
        resp = client.post(
            "/api/v1/exercises/alternatives",
            json={
                "exercise_id": "back_squat",
                "athlete_equipment": [],
            },
        )
        data = resp.json()
        # front_squat, high_bar_squat all require barbell+rack so should be absent
        alt_ids = [a["id"] for a in data["alternatives"]]
        assert "front_squat" not in alt_ids
        assert "high_bar_squat" not in alt_ids

    def test_alternative_fields_present(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/exercises/alternatives",
            json={
                "exercise_id": "back_squat",
                "athlete_equipment": ["barbell", "rack"],
            },
        )
        data = resp.json()
        if data["alternatives"]:
            alt = data["alternatives"][0]
            assert "id" in alt
            assert "name" in alt
            assert "patterns" in alt
            assert "tags" in alt
            assert "fatigue_cost" in alt
            assert "match_reason" in alt

    def test_empty_alternatives_returns_200_not_error(
        self, client: TestClient
    ) -> None:
        # back_squat with no equipment → no barbell exercises available
        resp = client.post(
            "/api/v1/exercises/alternatives",
            json={
                "exercise_id": "back_squat",
                "athlete_equipment": [],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "alternatives" in data
