"""Normalize user-supplied equipment strings to library identifiers.

The frontend (and user input) may send human-readable names with spaces
(e.g. "cable machine", "pull up bar") while the exercise library uses
underscore-separated canonical identifiers (e.g. "cable", "pullup_bar").
This module maps the common variants so the selector's equipment filter
works correctly without requiring the frontend to know internal IDs.
"""

from __future__ import annotations

# Maps any incoming string to its canonical library identifier.
# Keys are lowercased for case-insensitive matching.
_NORMALIZER: dict[str, str] = {
    # Cable variations
    "cable machine": "cable",
    "cable_machine": "cable",
    "cables": "cable",
    # Pull-up bar variations
    "pull up bar": "pullup_bar",
    "pull-up bar": "pullup_bar",
    "pullup bar": "pullup_bar",
    "chinup bar": "pullup_bar",
    "chin-up bar": "pullup_bar",
    "chin up bar": "pullup_bar",
    # Dip station variations
    "dip station": "dip_station",
    "dip bars": "dip_station",
    "dip bar": "dip_station",
    # Back raise bench variations
    "back raise bench": "back_extension_bench",
    "back extension bench": "back_extension_bench",
    "hyperextension bench": "back_extension_bench",
    "45 degree back extension": "back_extension_bench",
    # Smith machine — no library exercises require it; map to rack
    # so smith-machine users can still access barbell+rack exercises
    "smith machine": "rack",
    # Assisted dip machine — no library exercises require it; map to
    # dip_station so assisted-dip users can access dip exercises
    "assisted dip machine": "dip_station",
    "assisted dip": "dip_station",
    # Belt squat machine
    "belt squat machine": "belt_squat_machine",
    "belt squat": "belt_squat_machine",
    # Miscellaneous common variants
    "dumbbells": "dumbbell",
    "kettlebells": "kettlebell",
    "barbells": "barbell",
    "pull-up": "pullup_bar",
    "pullups": "pullup_bar",
}


def normalize_equipment(equipment: list[str]) -> list[str]:
    """Return a new list with each item normalized to its library identifier.

    Unknown strings are passed through unchanged so custom library entries
    are never silently dropped.
    """
    normalized: list[str] = []
    seen: set[str] = set()
    for item in equipment:
        canonical = _NORMALIZER.get(item.lower(), item)
        if canonical not in seen:
            seen.add(canonical)
            normalized.append(canonical)
    return normalized
