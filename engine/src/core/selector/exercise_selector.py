"""Exercise selector: picks exercises from the library based on criteria."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from src.core.selector.equipment_normalizer import normalize_equipment

if TYPE_CHECKING:
    from src.models.exercise_library import Exercise, ExerciseLibrary


class ExerciseSelector:
    def __init__(self, library: ExerciseLibrary) -> None:
        self._exercises = library.exercises

    def select(
        self,
        count: int,
        include_tags: list[str],
        exclude_tags: list[str] | None = None,
        prefer_tags: list[str] | None = None,
        athlete_equipment: list[str] | None = None,
        restrictions: list[str] | None = None,
        already_used_ids: set[str] | None = None,
        already_used_swap_groups: set[str] | None = None,
        seed: int | None = None,
    ) -> list[Exercise]:
        exclude_tags = exclude_tags or []
        prefer_tags = prefer_tags or []
        athlete_equipment = athlete_equipment or []
        restrictions = restrictions or []
        already_used_ids = already_used_ids or set()
        already_used_swap_groups = already_used_swap_groups or set()

        candidates = self._filter(
            include_tags=include_tags,
            exclude_tags=exclude_tags,
            athlete_equipment=normalize_equipment(athlete_equipment),
            restrictions=restrictions,
            already_used_ids=already_used_ids,
            already_used_swap_groups=already_used_swap_groups,
        )

        scored = self._score(candidates, prefer_tags)

        rng = random.Random(seed)
        return self._pick(scored, count, rng)

    def _filter(
        self,
        include_tags: list[str],
        exclude_tags: list[str],
        athlete_equipment: list[str],
        restrictions: list[str],
        already_used_ids: set[str],
        already_used_swap_groups: set[str],
    ) -> list[Exercise]:
        include_set = set(include_tags)
        exclude_set = set(exclude_tags)
        equip_set = set(athlete_equipment)
        restrict_set = set(restrictions)

        result: list[Exercise] = []
        for ex in self._exercises:
            ex_tags = set(ex.tags)

            if not (ex_tags & include_set):
                continue

            if ex_tags & exclude_set:
                continue

            if ex.equipment and not set(ex.equipment).issubset(equip_set):
                continue

            if restrict_set and set(ex.contraindications) & restrict_set:
                continue

            if ex.id in already_used_ids:
                continue

            if ex.swap_group and ex.swap_group in already_used_swap_groups:
                continue

            result.append(ex)

        return result

    def _score(
        self, candidates: list[Exercise], prefer_tags: list[str]
    ) -> list[tuple[float, Exercise]]:
        prefer_set = set(prefer_tags)
        scored: list[tuple[float, Exercise]] = []
        for ex in candidates:
            prefer_matches = len(set(ex.tags) & prefer_set)
            score = prefer_matches
            scored.append((score, ex))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    def _pick(
        self,
        scored: list[tuple[float, Exercise]],
        count: int,
        rng: random.Random,
    ) -> list[Exercise]:
        if not scored:
            return []

        max_score = scored[0][0]
        top_tier = [ex for s, ex in scored if s == max_score]
        lower_tier = [ex for s, ex in scored if s < max_score]

        rng.shuffle(top_tier)
        rng.shuffle(lower_tier)

        pool = top_tier + lower_tier
        return pool[:count]
