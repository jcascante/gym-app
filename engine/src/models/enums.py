from enum import StrEnum


class Pattern(StrEnum):
    SQUAT = "squat"
    HINGE = "hinge"
    LUNGE_UNILATERAL = "lunge_unilateral"
    HORIZONTAL_PUSH = "horizontal_push"
    HORIZONTAL_PULL = "horizontal_pull"
    VERTICAL_PUSH = "vertical_push"
    VERTICAL_PULL = "vertical_pull"
    CARRY = "carry"
    CORE_ANTI_EXTENSION = "core_anti_extension"
    CORE_ANTI_ROTATION = "core_anti_rotation"
    CORE_FLEXION = "core_flexion"
    ROTATION = "rotation"
    CONDITIONING_STEADY = "conditioning_steady"
    CONDITIONING_INTERVALS = "conditioning_intervals"


class Muscle(StrEnum):
    QUADS = "quads"
    HAMSTRINGS = "hamstrings"
    GLUTES = "glutes"
    ADDUCTORS = "adductors"
    CALVES = "calves"
    ERECTORS = "erectors"
    LATS = "lats"
    UPPER_BACK = "upper_back"
    CHEST = "chest"
    DELTS_ANTERIOR = "delts_anterior"
    DELTS_LATERAL = "delts_lateral"
    DELTS_POSTERIOR = "delts_posterior"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    FOREARMS_GRIP = "forearms_grip"
    ABS = "abs"
    OBLIQUES = "obliques"


class Level(StrEnum):
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class MainMethod(StrEnum):
    RPE = "RPE"
    PERCENT = "PERCENT"
    HYBRID = "HYBRID"


class HardSetRule(StrEnum):
    RIR_LE_4 = "RIR_LE_4"
    RPE_GE_6 = "RPE_GE_6"


class RoundingProfile(StrEnum):
    NONE = "none"
    PLATE_2P5KG = "plate_2p5kg"
    DB_2KG = "db_2kg"


class VolumeMetric(StrEnum):
    HARD_SETS_WEIGHTED = "hard_sets_weighted"
    TONNAGE = "tonnage"
    BOTH = "both"


class ConditioningMethod(StrEnum):
    HR_ZONES = "HR_ZONES"
    PACE = "PACE"
    POWER = "POWER"
    RPE = "RPE"


class HrZoneFormula(StrEnum):
    KARVONEN_HRR = "KARVONEN_HRR"
    PERCENT_HRMAX = "PERCENT_HRMAX"


class Modality(StrEnum):
    RUN = "run"
    ROW = "row"
    BIKE = "bike"
    MIXED = "mixed"


class BlockType(StrEnum):
    MAIN_LIFT = "main_lift"
    SECONDARY_LIFT = "secondary_lift"
    ACCESSORY = "accessory"
    CONDITIONING_STEADY = "conditioning_steady"
    CONDITIONING_INTERVALS = "conditioning_intervals"
    CIRCUIT = "circuit"
    MOBILITY = "mobility"
    WARMUP = "warmup"
    COOLDOWN = "cooldown"


class ExerciseLibraryRefType(StrEnum):
    FILE = "file"
    URL = "url"
    EMBEDDED = "embedded"


class ParameterFieldType(StrEnum):
    NUMBER = "number"
    STRING = "string"
    ENUM = "enum"
    BOOLEAN = "boolean"
    STRING_ARRAY = "string_array"
    NUMBER_ARRAY = "number_array"
    OBJECT = "object"
