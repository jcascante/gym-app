// --- Engine Program Definitions ---

export interface EngineProgramSummary {
  program_id: string;
  version: string;
  name: string | null;
  description: string | null;
  category: string | null;
  tags: string[];
  days_per_week: { min: number; max: number };
  weeks: { min: number; max: number };
}

export interface ParameterField {
  key: string;
  type: 'enum' | 'string' | 'number' | 'boolean' | 'string_array' | 'number_array' | 'object';
  required?: boolean;
  required_if?: string | null;
  visible_if?: string | null;
  default_expr?: string | null;
  min?: number | null;
  max?: number | null;
  enum?: string[];
  description?: string | null;
}

export interface EngineProgramDefinition extends EngineProgramSummary {
  parameter_spec: { fields: ParameterField[] };
  template: {
    weeks: { min: number; max: number };
    days_per_week: { min: number; max: number };
  };
}

// --- Prescription shapes ---

export interface StrengthPrescription {
  top_set: { sets: number; reps: number; target_rpe: number; load_kg: number };
  backoff: Array<{ sets: number; reps: number; load_kg: number }>;
  rounding_profile: string;
}

export interface RepsRangePrescription {
  sets: number;
  reps_range: [number, number];
  target_rir: number;
  load_note: string;
}

export interface ConditioningIntervalsPrescription {
  warmup_minutes: number;
  work: {
    intervals: number;
    seconds_each: number;
    intensity: { method: string; target: string };
  };
  rest_seconds: number;
  cooldown_minutes: number;
  notes: string | null;
}

export interface ConditioningSteadyPrescription {
  duration_minutes: number;
  intensity: { method: string; target: string };
  notes: string;
}

export type PrescriptionShape =
  | StrengthPrescription
  | RepsRangePrescription
  | ConditioningIntervalsPrescription
  | ConditioningSteadyPrescription;

// --- Generated Plan ---

export interface EngineBlock {
  block_id: string;
  type: string;
  exercise: { id: string; name: string };
  prescription: Record<string, unknown>;
}

export interface EngineSession {
  day: number;
  tags: string[];
  blocks: EngineBlock[];
  metrics?: {
    fatigue_score: number;
    volume_summary: Record<string, unknown>;
  };
}

export interface EngineWeek {
  week: number;
  sessions: EngineSession[];
}

export interface GeneratedPlan {
  program_id: string;
  program_version: string;
  generated_at: string;
  inputs_echo: Record<string, unknown>;
  weeks: EngineWeek[];
  warnings: string[];
  repairs: string[];
}

// --- Alternatives ---

export interface ExerciseAlternative {
  id: string;
  name: string;
  patterns: string[];
  tags: string[];
  swap_group: string | null;
  fatigue_cost: number;
  match_reason: 'swap_group' | 'pattern_match';
}

export interface AlternativesResponse {
  original_exercise_id: string;
  alternatives: ExerciseAlternative[];
}

// --- Saved Plan (our backend) ---

export interface SavedPlanSummary {
  id: string;
  client_id: string;
  subscription_id: string;
  name: string;
  notes: string | null;
  engine_program_id: string;
  engine_program_version: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  assignment_id: string | null;
}

export interface SavedPlanDetail extends SavedPlanSummary {
  inputs_echo: Record<string, unknown> | null;
  plan_data: GeneratedPlan;
}

export interface SavePlanRequest {
  name: string;
  notes?: string;
  engine_program_id: string;
  engine_program_version: string;
  inputs_echo?: Record<string, unknown>;
  plan_data: GeneratedPlan;
}
