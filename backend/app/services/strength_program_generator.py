"""
Strength Program Generator Service

This is the SINGLE SOURCE OF TRUTH for program calculations.
Frontend mirrors these calculations for preview, but backend regenerates on save.
"""
from typing import Dict, Tuple
from app.schemas.program import (
    ProgramInputs,
    MovementInput,
    MovementCalculations,
    ExerciseDetail,
    DayDetail,
    WeekDetail,
    ProgramPreview,
    CalculationConstants
)


class StrengthProgramGenerator:
    """
    Generates linear progression strength programs based on 5x5 methodology.

    Algorithm: Progressive overload using weekly linear progression
    Duration: 8 weeks
    Frequency: 4 sessions per week (Heavy-Light-Heavy-Light pattern)
    Protocol: 5x5 (weeks 1-5), 3x3 (week 6), 2x2 (week 7), Testing (week 8)
    """

    VERSION = "v1.0.0"
    BUILDER_TYPE = "strength_linear_5x5"

    # ========================================================================
    # CALCULATION CONSTANTS - Single source of truth
    # ========================================================================

    # Maps max reps at 80% of 1RM → weekly progression percentage
    # Lower reps at 80% = less capacity = need bigger jumps to reach target
    WEEKLY_JUMP_TABLE: Dict[int, int] = {
        20: 2, 19: 2, 18: 2, 17: 2, 16: 2,
        15: 3, 14: 3, 13: 3, 12: 3, 11: 3,
        10: 4, 9: 4, 8: 4, 7: 4, 6: 4,
        5: 5, 4: 5, 3: 5, 2: 5, 1: 5
    }

    # Maps max reps at 80% of 1RM → starting percentage for ramp-up test
    # Lower reps at 80% = less capacity = start heavier for 5RM test
    RAMP_UP_TABLE: Dict[int, int] = {
        20: 70, 19: 69, 18: 68, 17: 67, 16: 66,
        15: 65, 14: 64, 13: 63, 12: 62, 11: 61,
        10: 60, 9: 59, 8: 58, 7: 57, 6: 56,
        5: 55, 4: 54, 3: 53, 2: 52, 1: 51
    }

    # Sets and reps by week
    PROTOCOL_BY_WEEK: Dict[int, Tuple[int, int]] = {
        1: (5, 5), 2: (5, 5), 3: (5, 5), 4: (5, 5), 5: (5, 5),
        6: (3, 3),
        7: (2, 2),
        8: (1, 1),  # Testing week
    }

    # ========================================================================
    # Public API
    # ========================================================================

    @classmethod
    def get_constants(cls) -> CalculationConstants:
        """
        Return calculation constants for frontend to use.
        This ensures frontend calculations match backend.
        """
        return CalculationConstants(
            version=cls.VERSION,
            builder_type=cls.BUILDER_TYPE,
            weekly_jump_table=cls.WEEKLY_JUMP_TABLE,
            ramp_up_table=cls.RAMP_UP_TABLE,
            protocol_by_week={
                week: {"sets": sets, "reps": reps}
                for week, (sets, reps) in cls.PROTOCOL_BY_WEEK.items()
            }
        )

    @classmethod
    def generate_preview(cls, inputs: ProgramInputs) -> ProgramPreview:
        """
        Generate program preview without saving to database.
        Used for:
        1. Frontend validation (compare against frontend calculations)
        2. Preview before saving
        """
        calculated_data = cls._calculate_movement_data(inputs.movements)
        weeks = cls._generate_weeks(inputs, calculated_data)

        return ProgramPreview(
            algorithm_version=cls.VERSION,
            input_data=inputs.model_dump(),
            calculated_data=calculated_data,
            weeks=weeks
        )

    # ========================================================================
    # Calculation Methods
    # ========================================================================

    @classmethod
    def _calculate_movement_data(
        cls,
        movements: list[MovementInput]
    ) -> Dict[str, MovementCalculations]:
        """
        Calculate progression parameters for each movement.
        Returns dict keyed by movement name.
        """
        result = {}

        for movement in movements:
            # Weekly jump calculation
            weekly_jump_pct = cls.WEEKLY_JUMP_TABLE.get(
                movement.max_reps_at_80_percent,
                5  # Default to 5% if not in table
            )
            weekly_jump_lbs = round((movement.one_rm * weekly_jump_pct) / 100)

            # Ramp up calculation
            ramp_up_pct = cls.RAMP_UP_TABLE.get(
                movement.max_reps_at_80_percent,
                55  # Default to 55% if not in table
            )
            ramp_up_base_lbs = round((movement.one_rm * ramp_up_pct) / 100)

            result[movement.name] = MovementCalculations(
                name=movement.name,
                weekly_jump_percent=weekly_jump_pct,
                weekly_jump_lbs=weekly_jump_lbs,
                ramp_up_percent=ramp_up_pct,
                ramp_up_base_lbs=ramp_up_base_lbs
            )

        return result

    @classmethod
    def _generate_weeks(
        cls,
        inputs: ProgramInputs,
        calculated_data: Dict[str, MovementCalculations]
    ) -> list[WeekDetail]:
        """Generate all 8 weeks of training."""
        weeks = []

        for week_num in range(1, inputs.duration_weeks + 1):
            week = cls._generate_week(week_num, inputs, calculated_data)
            weeks.append(week)

        return weeks

    @classmethod
    def _generate_week(
        cls,
        week_num: int,
        inputs: ProgramInputs,
        calculated_data: Dict[str, MovementCalculations]
    ) -> WeekDetail:
        """Generate a single week of training."""
        week_name = cls._get_week_name(week_num)

        # Week 8 is testing week (different structure)
        if week_num == 8:
            days = [cls._generate_test_day(inputs)]
        else:
            # Generate 4 sessions: Heavy, Light, Heavy, Light
            days = []
            sets, reps = cls.PROTOCOL_BY_WEEK[week_num]

            for day_num in range(1, inputs.days_per_week + 1):
                is_heavy = (day_num % 2 == 1)  # Days 1,3 are heavy; 2,4 are light
                day = cls._generate_day(
                    day_num=day_num,
                    week_num=week_num,
                    inputs=inputs,
                    calculated_data=calculated_data,
                    sets=sets,
                    reps=reps,
                    is_heavy=is_heavy
                )
                days.append(day)

        return WeekDetail(
            week_number=week_num,
            name=week_name,
            days=days
        )

    @classmethod
    def _generate_day(
        cls,
        day_num: int,
        week_num: int,
        inputs: ProgramInputs,
        calculated_data: Dict[str, MovementCalculations],
        sets: int,
        reps: int,
        is_heavy: bool
    ) -> DayDetail:
        """Generate a single training day."""
        day_names = {
            1: "Monday",
            2: "Wednesday",
            3: "Friday",
            4: "Saturday"
        }

        intensity = "Heavy" if is_heavy else "Light"
        day_name = f"Session {day_num} - {intensity} Day"

        exercises = []
        for movement in inputs.movements:
            exercise = cls._calculate_exercise(
                movement=movement,
                week_num=week_num,
                calc_data=calculated_data[movement.name],
                sets=sets,
                reps=reps,
                is_heavy=is_heavy
            )
            exercises.append(exercise)

        return DayDetail(
            day_number=day_num,
            name=day_name,
            suggested_day_of_week=day_names.get(day_num),
            exercises=exercises
        )

    @classmethod
    def _calculate_exercise(
        cls,
        movement: MovementInput,
        week_num: int,
        calc_data: MovementCalculations,
        sets: int,
        reps: int,
        is_heavy: bool
    ) -> ExerciseDetail:
        """
        Calculate weight for a specific exercise.

        Progression logic:
        - Weeks 1-5: Linear progression toward target (5x5)
        - Week 6: Target + 1 jump (3x3)
        - Week 7: Target + 2 jumps (2x2)
        - Week 8: Testing (1RM)
        """
        # Calculate heavy weight for this week
        if week_num <= 5:
            # Linear progression: work backward from target weight
            # Week 1: target - 4 jumps
            # Week 5: target
            heavy_weight = movement.target_weight - ((5 - week_num) * calc_data.weekly_jump_lbs)
        elif week_num == 6:
            heavy_weight = movement.target_weight + calc_data.weekly_jump_lbs
        elif week_num == 7:
            heavy_weight = movement.target_weight + (2 * calc_data.weekly_jump_lbs)
        else:  # week 8
            heavy_weight = 0  # Testing week, no prescribed weight

        # Light weight is 80% of heavy
        weight = heavy_weight if is_heavy else round(heavy_weight * 0.8)

        # Calculate percentage of 1RM
        percentage_1rm = round((weight / movement.one_rm) * 100) if weight > 0 else None

        # Exercise name convention: uppercase for heavy, lowercase for light
        exercise_name = movement.name.upper() if is_heavy else movement.name.lower()

        return ExerciseDetail(
            exercise_name=exercise_name,
            sets=sets,
            reps=reps,
            weight_lbs=weight if weight > 0 else None,
            percentage_1rm=percentage_1rm,
            notes=""
        )

    @classmethod
    def _generate_test_day(cls, inputs: ProgramInputs) -> DayDetail:
        """Generate testing week day."""
        exercises = [
            ExerciseDetail(
                exercise_name=movement.name.upper(),
                sets=1,
                reps=1,
                weight_lbs=None,  # To be determined during test
                percentage_1rm=100,
                notes=f"Test new 1RM. Previous: {movement.one_rm} lbs"
            )
            for movement in inputs.movements
        ]

        return DayDetail(
            day_number=1,
            name="1RM Test Day",
            suggested_day_of_week="Wednesday",
            exercises=exercises
        )

    @classmethod
    def _get_week_name(cls, week_num: int) -> str:
        """Get descriptive name for the week."""
        week_names = {
            1: "Foundation Phase",
            2: "Building Phase - Week 2",
            3: "Building Phase - Week 3",
            4: "Building Phase - Week 4",
            5: "Building Phase - Week 5",
            6: "Intensification Phase",
            7: "Peak Phase",
            8: "Testing Week"
        }
        return week_names.get(week_num, f"Week {week_num}")
