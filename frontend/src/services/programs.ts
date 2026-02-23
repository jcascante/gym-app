/**
 * Programs API service
 *
 * Handles fetching, listing, and deleting program templates
 */

import { apiFetch } from './api';

// ============================================================================
// Types
// ============================================================================

export interface ProgramSummary {
  id: string;
  subscription_id: string | null;
  created_by_user_id: string | null;
  name: string;
  description: string | null;
  builder_type: string | null;
  algorithm_version: string | null;
  duration_weeks: number;
  days_per_week: number;
  is_template: boolean;
  is_public: boolean;
  times_assigned: number;
  status: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProgramListResponse {
  programs: ProgramSummary[];
  total: number;
}

export interface ExerciseDetail {
  id?: string;
  exercise_name: string;
  sets: number;
  reps: number;
  weight_lbs: number | null;
  percentage_1rm: number | null;
  notes: string;
}

export interface DayDetail {
  day_number: number;
  name: string;
  suggested_day_of_week: string | null;
  exercises: ExerciseDetail[];
}

export interface WeekDetail {
  week_number: number;
  name: string;
  days: DayDetail[];
}

export interface ProgramDetail extends ProgramSummary {
  input_data: Record<string, unknown>;
  calculated_data: Record<string, unknown>;
  weeks: WeekDetail[];
}

// ============================================================================
// Generate-for-Client Types
// ============================================================================

export interface MovementParam {
  name: string;
  one_rm: number;
  max_reps_at_80_percent: number;
  target_weight: number;
}

export interface GenerateForClientRequest {
  client_id: string;
  movements: MovementParam[];
  start_date?: string;
  notes?: string;
}

export interface GenerateForClientResponse {
  program_id: string;
  assignment_id: string;
  client_id: string;
  status: string;
}

export interface UpdateExerciseRequest {
  sets?: number;
  reps?: number;
  reps_target?: number;
  weight_lbs?: number;
  load_value?: number;
  notes?: string;
}

export interface UpdateExerciseResponse {
  exercise_id: string;
  sets: number;
  reps: number | null;
  reps_target: number | null;
  weight_lbs: number | null;
  load_value: number | null;
  notes: string | null;
  updated_at: string;
}

export interface PublishProgramResponse {
  program_id: string;
  status: string;
  published_at: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * List all program templates for the current coach's subscription
 */
export async function listPrograms(params?: {
  is_template?: boolean;
  search?: string;
}): Promise<ProgramListResponse> {
  const queryParams = new URLSearchParams();
  if (params?.is_template !== undefined) {
    queryParams.append('is_template', String(params.is_template));
  }
  if (params?.search) {
    queryParams.append('search', params.search);
  }
  const qs = queryParams.toString();
  return apiFetch<ProgramListResponse>(`/programs/${qs ? `?${qs}` : ''}`);
}

/**
 * Get full program details including weeks, days, and exercises
 */
export async function getProgramDetail(programId: string): Promise<ProgramDetail> {
  return apiFetch<ProgramDetail>(`/programs/${programId}`);
}

/**
 * Archive (soft-delete) a program by ID
 */
export async function deleteProgram(programId: string): Promise<{ message: string }> {
  return apiFetch<{ message: string }>(`/programs/${programId}`, {
    method: 'DELETE',
  });
}

/**
 * Generate a client-specific draft program from a template
 */
export async function generateForClient(
  templateId: string,
  data: GenerateForClientRequest
): Promise<GenerateForClientResponse> {
  return apiFetch<GenerateForClientResponse>(`/programs/${templateId}/generate-for-client`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

/**
 * Update a single exercise in a draft program
 */
export async function updateProgramExercise(
  programId: string,
  exerciseId: string,
  data: UpdateExerciseRequest
): Promise<UpdateExerciseResponse> {
  return apiFetch<UpdateExerciseResponse>(`/programs/${programId}/exercises/${exerciseId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

/**
 * Publish a draft program (makes it visible to the client)
 */
export async function publishProgram(programId: string): Promise<PublishProgramResponse> {
  return apiFetch<PublishProgramResponse>(`/programs/${programId}/publish`, {
    method: 'POST',
  });
}
