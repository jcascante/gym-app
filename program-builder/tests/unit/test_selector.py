"""Tests for the exercise selector -- written FIRST (TDD RED phase)."""

import pytest

from src.core.selector.exercise_selector import ExerciseSelector as Selector
from src.models.exercise_library import Exercise, ExerciseLibrary


def _make_exercise(
    id: str,
    tags: list[str],
    equipment: list[str] | None = None,
    swap_group: str | None = None,
    fatigue_cost: float = 0.5,
    contraindications: list[str] | None = None,
    patterns: list[str] | None = None,
    muscles: dict[str, float] | None = None,
) -> Exercise:
    return Exercise(
        id=id,
        name=id.replace("_", " ").title(),
        patterns=patterns or ["squat"],
        muscles=muscles or {"quads": 0.5},
        equipment=equipment or [],
        swap_group=swap_group,
        fatigue_cost=fatigue_cost,
        contraindications=contraindications or [],
        tags=tags,
    )


@pytest.fixture
def library() -> ExerciseLibrary:
    return ExerciseLibrary(
        version="1.0.0",
        patterns=["squat", "hinge"],
        muscles=["quads", "glutes", "hamstrings"],
        exercises=[
            _make_exercise(
                "back_squat",
                tags=["main", "squat_main", "barbell"],
                equipment=["barbell", "rack"],
                swap_group="squat_main",
                fatigue_cost=0.9,
            ),
            _make_exercise(
                "front_squat",
                tags=["main", "squat_main", "barbell"],
                equipment=["barbell", "rack"],
                swap_group="squat_main",
                fatigue_cost=0.85,
            ),
            _make_exercise(
                "goblet_squat",
                tags=["accessory", "squat_secondary", "dumbbell"],
                equipment=["dumbbells"],
                swap_group="squat_secondary",
                fatigue_cost=0.4,
            ),
            _make_exercise(
                "leg_extension",
                tags=["accessory", "quads_isolation"],
                equipment=["machine"],
                fatigue_cost=0.2,
            ),
            _make_exercise(
                "leg_curl",
                tags=["accessory", "hamstrings_isolation"],
                equipment=["machine"],
                fatigue_cost=0.2,
                patterns=["hinge"],
                muscles={"hamstrings": 0.8},
            ),
            _make_exercise(
                "barbell_row",
                tags=["secondary", "horizontal_pull_secondary", "barbell"],
                equipment=["barbell"],
                swap_group="h_pull",
                fatigue_cost=0.6,
                patterns=["horizontal_pull"],
                muscles={"upper_back": 0.8},
            ),
            _make_exercise(
                "cable_row",
                tags=["accessory", "horizontal_pull_accessory", "cable"],
                equipment=["cable"],
                swap_group="h_pull",
                fatigue_cost=0.35,
                patterns=["horizontal_pull"],
                muscles={"upper_back": 0.6},
            ),
            _make_exercise(
                "chin_up",
                tags=["accessory", "vertical_pull_accessory"],
                equipment=["pullup_bar"],
                fatigue_cost=0.5,
                patterns=["vertical_pull"],
                muscles={"lats": 0.8},
            ),
            _make_exercise(
                "bodyweight_squat",
                tags=["accessory", "squat_bodyweight"],
                equipment=[],
                fatigue_cost=0.1,
                contraindications=["knee_pain"],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Tag Filtering
# ---------------------------------------------------------------------------

class TestTagFiltering:
    def test_include_tags_filters_correctly(self, library: ExerciseLibrary) -> None:
        selector = Selector(library)
        results = selector.select(
            count=1,
            include_tags=["squat_main"],
            athlete_equipment=["barbell", "rack"],
        )
        assert len(results) == 1
        assert results[0].id in ("back_squat", "front_squat")

    def test_include_tags_multiple_matches(
        self, library: ExerciseLibrary
    ) -> None:
        selector = Selector(library)
        results = selector.select(
            count=2,
            include_tags=["squat_main"],
            athlete_equipment=["barbell", "rack"],
        )
        assert len(results) == 2
        ids = {r.id for r in results}
        assert ids == {"back_squat", "front_squat"}

    def test_exclude_tags(self, library: ExerciseLibrary) -> None:
        selector = Selector(library)
        results = selector.select(
            count=5,
            include_tags=["accessory"],
            exclude_tags=["quads_isolation"],
            athlete_equipment=["machine", "dumbbells", "cable", "pullup_bar"],
        )
        for ex in results:
            assert "quads_isolation" not in ex.tags

    def test_no_matching_tags_returns_empty(
        self, library: ExerciseLibrary
    ) -> None:
        selector = Selector(library)
        results = selector.select(
            count=1,
            include_tags=["nonexistent_tag"],
            athlete_equipment=["barbell"],
        )
        assert len(results) == 0


# ---------------------------------------------------------------------------
# Equipment Filtering
# ---------------------------------------------------------------------------

class TestEquipmentFiltering:
    def test_exercises_requiring_unavailable_equipment_excluded(
        self, library: ExerciseLibrary
    ) -> None:
        selector = Selector(library)
        results = selector.select(
            count=5,
            include_tags=["accessory"],
            athlete_equipment=["dumbbells"],
        )
        for ex in results:
            for eq in ex.equipment:
                assert eq in ["dumbbells", ""], (
                    f"Exercise {ex.id} requires {eq} which is not available"
                )

    def test_bodyweight_exercise_always_available(
        self, library: ExerciseLibrary
    ) -> None:
        selector = Selector(library)
        results = selector.select(
            count=1,
            include_tags=["squat_bodyweight"],
            athlete_equipment=[],
        )
        assert len(results) == 1
        assert results[0].id == "bodyweight_squat"


# ---------------------------------------------------------------------------
# Contraindications
# ---------------------------------------------------------------------------

class TestContraindications:
    def test_restriction_excludes_exercise(
        self, library: ExerciseLibrary
    ) -> None:
        selector = Selector(library)
        results = selector.select(
            count=1,
            include_tags=["squat_bodyweight"],
            athlete_equipment=[],
            restrictions=["knee_pain"],
        )
        assert len(results) == 0

    def test_no_restriction_includes_exercise(
        self, library: ExerciseLibrary
    ) -> None:
        selector = Selector(library)
        results = selector.select(
            count=1,
            include_tags=["squat_bodyweight"],
            athlete_equipment=[],
            restrictions=[],
        )
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Prefer Tags (Scoring)
# ---------------------------------------------------------------------------

class TestPreferTags:
    def test_prefer_barbell_scores_higher(
        self, library: ExerciseLibrary
    ) -> None:
        selector = Selector(library)
        results = selector.select(
            count=1,
            include_tags=["horizontal_pull_secondary", "horizontal_pull_accessory"],
            prefer_tags=["barbell"],
            athlete_equipment=["barbell", "cable"],
        )
        assert results[0].id == "barbell_row"

    def test_without_prefer_any_match_possible(
        self, library: ExerciseLibrary
    ) -> None:
        selector = Selector(library)
        results = selector.select(
            count=1,
            include_tags=["horizontal_pull_secondary", "horizontal_pull_accessory"],
            athlete_equipment=["barbell", "cable"],
        )
        assert results[0].id in ("barbell_row", "cable_row")


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

class TestDeduplication:
    def test_no_duplicate_exercises_in_results(
        self, library: ExerciseLibrary
    ) -> None:
        selector = Selector(library)
        results = selector.select(
            count=3,
            include_tags=["accessory"],
            athlete_equipment=["machine", "dumbbells", "cable", "pullup_bar"],
        )
        ids = [r.id for r in results]
        assert len(ids) == len(set(ids))

    def test_previously_used_exercises_excluded(
        self, library: ExerciseLibrary
    ) -> None:
        selector = Selector(library)
        results = selector.select(
            count=1,
            include_tags=["squat_main"],
            athlete_equipment=["barbell", "rack"],
            already_used_ids={"back_squat"},
        )
        assert len(results) == 1
        assert results[0].id == "front_squat"

    def test_previously_used_swap_group_excluded(
        self, library: ExerciseLibrary
    ) -> None:
        selector = Selector(library)
        results = selector.select(
            count=1,
            include_tags=["squat_main"],
            athlete_equipment=["barbell", "rack"],
            already_used_swap_groups={"squat_main"},
        )
        assert len(results) == 0


# ---------------------------------------------------------------------------
# Seed (Determinism)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_seed_same_results(self, library: ExerciseLibrary) -> None:
        selector = Selector(library)
        r1 = selector.select(
            count=1,
            include_tags=["accessory"],
            athlete_equipment=["machine", "dumbbells", "cable", "pullup_bar"],
            seed=42,
        )
        r2 = selector.select(
            count=1,
            include_tags=["accessory"],
            athlete_equipment=["machine", "dumbbells", "cable", "pullup_bar"],
            seed=42,
        )
        assert r1[0].id == r2[0].id

    def test_different_seed_may_differ(
        self, library: ExerciseLibrary
    ) -> None:
        selector = Selector(library)
        results_by_seed: dict[int, str] = {}
        for seed in range(50):
            r = selector.select(
                count=1,
                include_tags=["accessory"],
                athlete_equipment=[
                    "machine", "dumbbells", "cable", "pullup_bar",
                ],
                seed=seed,
            )
            if r:
                results_by_seed[seed] = r[0].id
        assert len(set(results_by_seed.values())) > 1


# ---------------------------------------------------------------------------
# Count
# ---------------------------------------------------------------------------

class TestCount:
    def test_count_1(self, library: ExerciseLibrary) -> None:
        selector = Selector(library)
        results = selector.select(
            count=1,
            include_tags=["squat_main"],
            athlete_equipment=["barbell", "rack"],
        )
        assert len(results) == 1

    def test_count_exceeds_available(
        self, library: ExerciseLibrary
    ) -> None:
        selector = Selector(library)
        results = selector.select(
            count=10,
            include_tags=["squat_main"],
            athlete_equipment=["barbell", "rack"],
        )
        assert len(results) <= 2

    def test_count_2_arms_example(self, library: ExerciseLibrary) -> None:
        """Like the d4_acc2 block that requests count=2 for biceps+triceps."""
        selector = Selector(library)
        results = selector.select(
            count=2,
            include_tags=["squat_main"],
            athlete_equipment=["barbell", "rack"],
        )
        assert len(results) == 2


# ---------------------------------------------------------------------------
# Integration with Real Library
# ---------------------------------------------------------------------------

class TestRealLibrary:
    def test_select_from_real_library(self, data_dir) -> None:
        import json

        raw = json.loads((data_dir / "exercise_library_v1.json").read_text())
        lib = ExerciseLibrary.model_validate(raw)
        selector = Selector(lib)
        results = selector.select(
            count=1,
            include_tags=["squat_main"],
            athlete_equipment=["barbell", "rack"],
            seed=42,
        )
        assert len(results) == 1
        assert "squat" in results[0].patterns

    def test_select_hinge_secondary(self, data_dir) -> None:
        import json

        raw = json.loads((data_dir / "exercise_library_v1.json").read_text())
        lib = ExerciseLibrary.model_validate(raw)
        selector = Selector(lib)
        results = selector.select(
            count=1,
            include_tags=["hinge_secondary"],
            prefer_tags=["barbell"],
            athlete_equipment=["barbell", "rack", "dumbbells"],
            seed=42,
        )
        assert len(results) == 1

    def test_select_core(self, data_dir) -> None:
        import json

        raw = json.loads((data_dir / "exercise_library_v1.json").read_text())
        lib = ExerciseLibrary.model_validate(raw)
        selector = Selector(lib)
        results = selector.select(
            count=1,
            include_tags=["core"],
            athlete_equipment=["cable"],
            seed=42,
        )
        assert len(results) == 1

    def test_select_conditioning(self, data_dir) -> None:
        import json

        raw = json.loads((data_dir / "exercise_library_v1.json").read_text())
        lib = ExerciseLibrary.model_validate(raw)
        selector = Selector(lib)
        results = selector.select(
            count=1,
            include_tags=["conditioning"],
            prefer_tags=["run"],
            athlete_equipment=[],
            seed=42,
        )
        assert len(results) == 1
