from pydantic import BaseModel, Field


class Exercise(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    patterns: list[str] = Field(min_length=1)
    muscles: dict[str, float] = Field(default_factory=dict)
    equipment: list[str] = Field(default_factory=list)
    swap_group: str | None = None
    fatigue_cost: float = Field(ge=0, le=2)
    contraindications: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: object) -> None:
        for key, val in self.muscles.items():
            if val < 0 or val > 1.5:
                raise ValueError(
                    f"Muscle activation for '{key}' must be between 0 and 1.5, got {val}"
                )


class ExerciseLibrary(BaseModel):
    version: str
    patterns: list[str]
    muscles: list[str]
    exercises: list[Exercise] = Field(min_length=1)
