import type { ProgramType, ExerciseCategory, BlockType } from "./types";

export interface CategoryTags {
  include_tags: string[];
}

export const CATEGORY_TAGS: Record<ExerciseCategory, CategoryTags> = {
  squat: { include_tags: ["squat_main", "squat"] },
  hip_hinge: { include_tags: ["hinge_main", "hinge", "deadlift"] },
  horizontal_push: { include_tags: ["horizontal_push"] },
  horizontal_pull: { include_tags: ["horizontal_pull"] },
  vertical_push: { include_tags: ["vertical_push"] },
  vertical_pull: { include_tags: ["vertical_pull"] },
  core: { include_tags: ["core_anti_extension", "core_flexion", "core_anti_rotation"] },
  conditioning: { include_tags: ["conditioning"] },
};

export const BLOCK_TYPE_DEFAULT_STYLE: Record<BlockType, string> = {
  main_lift: "top_set_plus_backoff",
  accessory: "reps_range_rir",
  conditioning: "steady_state",
};

export interface ParameterSpecField {
  key: string;
  type: string;
  enum?: string[];
  required: boolean;
  required_if?: string;
  default_expr?: string;
  min?: number;
  description?: string;
}

export interface ProgramPreset {
  parameter_spec: { fields: ParameterSpecField[] };
  rules: Record<string, unknown>;
  validation: Record<string, unknown>;
}

export const PROGRAM_PRESETS: Record<ProgramType, ProgramPreset> = {
  strength: {
    parameter_spec: {
      fields: [
        {
          key: "athlete.level",
          type: "enum",
          enum: ["novice", "intermediate", "advanced"],
          required: true,
        },
        {
          key: "athlete.equipment",
          type: "string_array",
          required: true,
        },
        {
          key: "athlete.restrictions",
          type: "string_array",
          required: false,
          default_expr: "[]",
        },
        {
          key: "rules.rounding_profile",
          type: "enum",
          enum: ["none", "plate_2p5kg", "kb_4kg"],
          required: true,
          default_expr: "'plate_2p5kg'",
        },
      ],
    },
    rules: {
      expression_language: "v1",
      rounding_profiles: {
        none: { type: "none" },
        plate_2p5kg: { type: "plate", increment_kg: 2.5 },
        kb_4kg: { type: "kettlebell", increment_kg: 4.0 },
      },
      defaults: {
        rounding_profile_key_expr: "ctx.rules.rounding_profile",
      },
      selection: {
        respect_equipment: true,
        respect_contraindications: true,
        avoid_same_exercise_within_days: 2,
        avoid_same_swap_group_within_days: 2,
      },
      fatigue_model: {
        per_set_expr: "exercise.fatigue_cost * intensity_factor",
      },
    },
    validation: {
      hard: {
        max_weekly_volume_by_key: {
          key_expr: "muscle",
          limit_expr: "choose(ctx.athlete.level,{'novice':16,'intermediate':20,'advanced':24})",
        },
        max_fatigue_per_session_expr: "12",
        max_fatigue_per_week_expr: "42",
      },
      soft: { warnings: [] },
      repair: {
        protected_block_types: ["main_lift"],
        strategy_order: [
          "reduce_accessory_sets",
          "swap_to_lower_fatigue_variant",
          "drop_optional_blocks",
        ],
        limits: {
          max_repairs_per_session: 8,
          max_repairs_per_plan: 40,
        },
      },
    },
  },
  hypertrophy: {
    parameter_spec: {
      fields: [
        {
          key: "athlete.level",
          type: "enum",
          enum: ["novice", "intermediate", "advanced"],
          required: true,
        },
        {
          key: "athlete.equipment",
          type: "string_array",
          required: true,
        },
        {
          key: "athlete.restrictions",
          type: "string_array",
          required: false,
          default_expr: "[]",
        },
      ],
    },
    rules: {
      expression_language: "v1",
      selection: {
        respect_equipment: true,
        respect_contraindications: true,
        avoid_same_exercise_within_days: 2,
        avoid_same_swap_group_within_days: 2,
      },
      fatigue_model: {
        per_set_expr: "exercise.fatigue_cost * intensity_factor",
      },
    },
    validation: {
      hard: {
        max_weekly_volume_by_key: {
          key_expr: "muscle",
          limit_expr: "choose(ctx.athlete.level,{'novice':20,'intermediate':26,'advanced':32})",
        },
        max_fatigue_per_session_expr: "14",
        max_fatigue_per_week_expr: "52",
      },
      soft: { warnings: [] },
      repair: {
        protected_block_types: ["main_lift"],
        strategy_order: [
          "reduce_accessory_sets",
          "swap_to_lower_fatigue_variant",
          "drop_optional_blocks",
        ],
        limits: {
          max_repairs_per_session: 8,
          max_repairs_per_plan: 40,
        },
      },
    },
  },
  conditioning: {
    parameter_spec: {
      fields: [
        {
          key: "athlete.level",
          type: "enum",
          enum: ["novice", "intermediate", "advanced"],
          required: true,
        },
        {
          key: "conditioning.method",
          type: "enum",
          enum: ["steady_state", "hiit", "circuits"],
          required: true,
          default_expr: "'steady_state'",
        },
      ],
    },
    rules: {
      expression_language: "v1",
      selection: {
        respect_equipment: false,
        respect_contraindications: true,
      },
    },
    validation: {
      hard: {
        max_fatigue_per_session_expr: "10",
        max_fatigue_per_week_expr: "36",
      },
      soft: { warnings: [] },
      repair: {
        protected_block_types: [],
        strategy_order: ["drop_optional_blocks"],
        limits: {
          max_repairs_per_session: 4,
          max_repairs_per_plan: 20,
        },
      },
    },
  },
};
