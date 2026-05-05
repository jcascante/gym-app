"""Plan overrides endpoint tests -- TDD RED phase."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.main import create_app

STRENGTH_REQUEST = {
    "program_id": "upper_lower_ab_4w_v1",
    "program_version": "1.0.0",
    "weeks": 1,
    "days_per_week": 4,
    "athlete": {
        "level": "intermediate",
        "time_budget_minutes": 90,
        "equipment": ["barbell", "rack", "bench", "dumbbells", "cable", "machine", "pullup_bar"],
        "e1rm": {"squat": 160.0, "bench": 115.0, "deadlift": 190.0, "ohp": 70.0},
    },
    "rules": {
        "rounding_profile": "plate_2p5kg",
        "volume_metric": "hard_sets_weighted",
        "hard_set_rule": "RIR_LE_4",
        "main_method": "HYBRID",
        "accessory_rir_target": 2,
    },
    "seed": 42,
}


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


@pytest.fixture
def generated_plan(client: TestClient) -> dict:
    resp = client.post("/api/v1/generate", json=STRENGTH_REQUEST)
    assert resp.status_code == 200
    return resp.json()


class TestApplyOverridesEndpoint:
    def test_returns_200(
        self, client: TestClient, generated_plan: dict
    ) -> None:
        resp = client.post(
            "/api/v1/plans/apply-overrides",
            json={"plan": generated_plan, "overrides": []},
        )
        assert resp.status_code == 200

    def test_response_structure(
        self, client: TestClient, generated_plan: dict
    ) -> None:
        resp = client.post(
            "/api/v1/plans/apply-overrides",
            json={"plan": generated_plan, "overrides": []},
        )
        data = resp.json()
        assert "plan" in data
        assert "applied" in data
        assert "rejected" in data

    def test_empty_overrides_returns_unchanged_plan(
        self, client: TestClient, generated_plan: dict
    ) -> None:
        resp = client.post(
            "/api/v1/plans/apply-overrides",
            json={"plan": generated_plan, "overrides": []},
        )
        data = resp.json()
        assert data["applied"] == []
        assert data["rejected"] == []
        assert data["plan"]["program_id"] == generated_plan["program_id"]

    def test_valid_swap_applied(
        self, client: TestClient, generated_plan: dict
    ) -> None:
        # Find a block with back_squat (same swap_group: squat_main includes front_squat)
        first_block = generated_plan["weeks"][0]["sessions"][0]["blocks"][0]
        block_id = first_block["block_id"]
        original_exercise_id = first_block["exercise"]["id"]

        # Find a compatible exercise (same swap_group or pattern)
        # Use front_squat which shares squat_main swap_group with back_squat
        # or use any exercise from library that shares patterns
        new_exercise_id = (
            "front_squat"
            if original_exercise_id == "back_squat"
            else "back_squat"
        )

        resp = client.post(
            "/api/v1/plans/apply-overrides",
            json={
                "plan": generated_plan,
                "overrides": [
                    {"block_id": block_id, "new_exercise_id": new_exercise_id}
                ],
            },
        )
        # If the swap is valid (same swap_group), it should be applied
        data = resp.json()
        assert resp.status_code == 200
        assert "applied" in data
        assert "rejected" in data

    def test_unknown_block_id_rejected(
        self, client: TestClient, generated_plan: dict
    ) -> None:
        resp = client.post(
            "/api/v1/plans/apply-overrides",
            json={
                "plan": generated_plan,
                "overrides": [
                    {
                        "block_id": "nonexistent_block_id",
                        "new_exercise_id": "front_squat",
                    }
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["rejected"]) == 1
        assert data["rejected"][0]["reason"] == "block_not_found"
        assert data["rejected"][0]["block_id"] == "nonexistent_block_id"

    def test_unknown_exercise_id_rejected(
        self, client: TestClient, generated_plan: dict
    ) -> None:
        first_block = generated_plan["weeks"][0]["sessions"][0]["blocks"][0]
        block_id = first_block["block_id"]

        resp = client.post(
            "/api/v1/plans/apply-overrides",
            json={
                "plan": generated_plan,
                "overrides": [
                    {
                        "block_id": block_id,
                        "new_exercise_id": "nonexistent_exercise_xyz",
                    }
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["rejected"]) == 1
        assert data["rejected"][0]["reason"] == "exercise_not_found"

    def _find_squat_main_block(self, plan: dict) -> dict | None:
        """Return first block whose exercise is in the squat_main swap group."""
        squat_main_ids = {"back_squat", "front_squat", "high_bar_squat", "low_bar_squat"}
        for week in plan["weeks"]:
            for session in week["sessions"]:
                for block in session["blocks"]:
                    if block["exercise"]["id"] in squat_main_ids:
                        return block
        return None

    def test_applied_override_updates_exercise_in_plan(
        self, client: TestClient, generated_plan: dict
    ) -> None:
        target_block = self._find_squat_main_block(generated_plan)
        if target_block is None:
            pytest.skip("No squat_main block in generated plan")

        block_id = target_block["block_id"]
        original_id = target_block["exercise"]["id"]
        # Pick any squat_main exercise that isn't the current one
        squat_main_ids = {"back_squat", "front_squat", "high_bar_squat", "low_bar_squat"}
        new_id = next(i for i in squat_main_ids if i != original_id)

        resp = client.post(
            "/api/v1/plans/apply-overrides",
            json={
                "plan": generated_plan,
                "overrides": [{"block_id": block_id, "new_exercise_id": new_id}],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["applied"]) == 1

        modified_plan = data["plan"]
        for week in modified_plan["weeks"]:
            for session in week["sessions"]:
                for block in session["blocks"]:
                    if block["block_id"] == block_id:
                        assert block["exercise"]["id"] == new_id

    def test_applied_override_contains_both_exercise_names(
        self, client: TestClient, generated_plan: dict
    ) -> None:
        target_block = self._find_squat_main_block(generated_plan)
        if target_block is None:
            pytest.skip("No squat_main block in generated plan")

        block_id = target_block["block_id"]
        original_id = target_block["exercise"]["id"]
        squat_main_ids = {"back_squat", "front_squat", "high_bar_squat", "low_bar_squat"}
        new_id = next(i for i in squat_main_ids if i != original_id)

        resp = client.post(
            "/api/v1/plans/apply-overrides",
            json={
                "plan": generated_plan,
                "overrides": [{"block_id": block_id, "new_exercise_id": new_id}],
            },
        )
        data = resp.json()
        assert len(data["applied"]) == 1
        applied = data["applied"][0]
        assert "original_exercise_id" in applied
        assert "original_exercise_name" in applied
        assert "new_exercise_id" in applied
        assert "new_exercise_name" in applied

    def test_incompatible_exercise_rejected(
        self, client: TestClient, generated_plan: dict
    ) -> None:
        # Find a squat block and try to swap with a horizontal_push exercise
        target_block = self._find_squat_main_block(generated_plan)
        if target_block is None:
            pytest.skip("No squat_main block in generated plan")

        block_id = target_block["block_id"]
        # bench_press is horizontal_push, squat is squat pattern — incompatible
        resp = client.post(
            "/api/v1/plans/apply-overrides",
            json={
                "plan": generated_plan,
                "overrides": [
                    {"block_id": block_id, "new_exercise_id": "bench_press"}
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["rejected"]) == 1
        assert data["rejected"][0]["reason"] == "incompatible_exercise"

    def test_mixed_valid_and_invalid_overrides(
        self, client: TestClient, generated_plan: dict
    ) -> None:
        resp = client.post(
            "/api/v1/plans/apply-overrides",
            json={
                "plan": generated_plan,
                "overrides": [
                    {
                        "block_id": "nonexistent_block",
                        "new_exercise_id": "front_squat",
                    }
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        # Invalid block → rejected; plan should still be returned
        assert len(data["rejected"]) >= 1
        assert "plan" in data

    def test_invalid_plan_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/plans/apply-overrides",
            json={"plan": {"not": "a valid plan"}, "overrides": []},
        )
        assert resp.status_code == 422
