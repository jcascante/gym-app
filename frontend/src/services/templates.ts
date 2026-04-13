/**
 * Template browsing and self-service program start service.
 */

import { apiFetch } from './api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface TemplateListItem {
  id: string;
  source: 'engine' | 'coach';
  name: string;
  description?: string;
  program_type?: string;
  difficulty_level?: string;
  duration_weeks: number;
  days_per_week: number;
  tags: string[];
  times_assigned: number;
}

export interface TemplateListResponse {
  templates: TemplateListItem[];
  total: number;
}

export interface ExercisePrescription {
  id: string;
  exercise_name: string;
  sets: number;
  reps?: number;
  reps_target?: number;
  weight_lbs?: number;
  rpe_target?: number;
  percentage_1rm?: number;
  rest_seconds?: number;
  notes?: string;
  coaching_cues?: string;
  exercise_order?: number;
}

export interface TodayWorkoutResponse {
  assignment_id: string;
  program_day_id: string;
  week_number: number;
  day_number: number;
  day_name: string;
  exercises: ExercisePrescription[];
  current_week: number;
  current_day: number;
  progress_percentage: number;
  progress_health: 'green' | 'yellow' | 'red';
}

export interface AssignmentState {
  id: string;
  program_id: string;
  client_id: string;
  assignment_name?: string;
  start_date: string;
  end_date?: string;
  status: string;
  current_week: number;
  current_day: number;
  workouts_completed: number;
  workouts_skipped: number;
  progress_percentage: number;
  progress_health: 'green' | 'yellow' | 'red';
  client_rating?: number;
  client_feedback?: string;
}

export interface SelfStartResponse {
  assignment_id: string;
  program_id: string;
  start_date: string;
  end_date: string;
  status: string;
}

export interface SetLogRequest {
  set_number: number;
  actual_reps?: number;
  actual_weight_lbs?: number;
  actual_rpe?: number;
  notes?: string;
}

export interface ExerciseLogRequest {
  program_day_exercise_id?: string;
  exercise_name: string;
  sets: SetLogRequest[];
}

export interface WorkoutLogExtendedRequest {
  assignment_id: string;
  program_day_id?: string;
  day_status: 'completed' | 'skipped' | 'partial';
  duration_minutes?: string;
  session_rating?: number;
  notes?: string;
  exercise_logs: ExerciseLogRequest[];
}

export interface WorkoutLogExtendedResponse {
  workout_log_id: string;
  assignment_id: string;
  program_day_id?: string;
  day_status?: string;
  duration_minutes?: string;
  session_rating?: number;
  exercise_logs: unknown[];
  current_week: number;
  current_day: number;
  assignment_status: string;
  progress_percentage: number;
  progress_health: string;
}

// ---------------------------------------------------------------------------
// Program detail (full tree for started programs)
// ---------------------------------------------------------------------------

export interface ProgramExercise {
  id: string;
  exercise_name: string;
  sets: number;
  reps: number;
  weight_lbs?: number;
  notes?: string;
}

export interface ProgramDay {
  id: string;
  day_number: number;
  name: string;
  exercises: ProgramExercise[];
}

export interface ProgramWeek {
  week_number: number;
  name: string;
  days: ProgramDay[];
}

export interface ProgramDetail {
  id: string;
  name: string;
  description?: string;
  duration_weeks: number;
  days_per_week: number;
  weeks: ProgramWeek[];
}

export async function getProgramDetail(programId: string): Promise<ProgramDetail> {
  return apiFetch<ProgramDetail>(`/programs/${programId}`);
}

// ---------------------------------------------------------------------------
// Template browsing
// ---------------------------------------------------------------------------

export interface TemplateFilters {
  source?: 'engine' | 'coach';
  difficulty?: string;
  duration_weeks?: number;
}

export async function listTemplates(filters: TemplateFilters = {}): Promise<TemplateListResponse> {
  const params = new URLSearchParams();
  if (filters.source) params.set('source', filters.source);
  if (filters.difficulty) params.set('difficulty', filters.difficulty);
  if (filters.duration_weeks) params.set('duration_weeks', String(filters.duration_weeks));
  const qs = params.toString();
  return apiFetch<TemplateListResponse>(`/programs/templates${qs ? `?${qs}` : ''}`);
}

export async function getTemplateDetail(source: 'engine' | 'coach', templateId: string): Promise<unknown> {
  return apiFetch<unknown>(`/programs/templates/${templateId}?source=${source}`);
}

export async function previewTemplate(
  templateId: string,
  body: { source: 'engine' | 'coach'; inputs?: Record<string, unknown>; movements?: unknown[] }
): Promise<unknown> {
  return apiFetch<unknown>(`/programs/templates/${templateId}/preview`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function selfStartProgram(
  templateId: string,
  body: {
    source: 'engine' | 'coach';
    inputs?: Record<string, unknown>;
    movements?: unknown[];
    start_date?: string;
    assignment_name?: string;
  }
): Promise<SelfStartResponse> {
  return apiFetch<SelfStartResponse>(`/programs/templates/${templateId}/start`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// ---------------------------------------------------------------------------
// Assignment management
// ---------------------------------------------------------------------------

export async function getAssignment(assignmentId: string): Promise<AssignmentState> {
  return apiFetch<AssignmentState>(`/workouts/assignments/${assignmentId}`);
}

export async function getTodayWorkout(
  assignmentId: string,
  week?: number,
  day?: number,
): Promise<TodayWorkoutResponse> {
  const params = new URLSearchParams();
  if (week !== undefined) params.set('week', String(week));
  if (day !== undefined) params.set('day', String(day));
  const qs = params.toString();
  return apiFetch<TodayWorkoutResponse>(`/workouts/assignments/${assignmentId}/today${qs ? `?${qs}` : ''}`);
}

export interface DayLogSummary {
  workout_log_id: string;
  program_day_id: string | null;
  day_status: string;
  workout_date: string;
}

export async function getAssignmentLogs(assignmentId: string): Promise<DayLogSummary[]> {
  return apiFetch<DayLogSummary[]>(`/workouts/assignments/${assignmentId}/logs`);
}

export interface PreviousSetLog {
  set_number: number;
  actual_reps: number | null;
  actual_weight_lbs: number | null;
  actual_rpe: number | null;
  notes: string | null;
}

export interface PreviousExerciseLog {
  exercise_name: string;
  program_day_exercise_id: string | null;
  sets: PreviousSetLog[];
}

export interface WorkoutFullDetail {
  workout_log_id: string;
  day_status: string | null;
  duration_minutes: string | null;
  session_rating: number | null;
  notes: string | null;
  exercise_logs: PreviousExerciseLog[];
}

export async function getWorkoutDetail(workoutLogId: string): Promise<WorkoutFullDetail> {
  return apiFetch<WorkoutFullDetail>(`/workouts/${workoutLogId}/detail`);
}

export async function logWorkout(body: WorkoutLogExtendedRequest): Promise<WorkoutLogExtendedResponse> {
  return apiFetch<WorkoutLogExtendedResponse>('/workouts/log', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function submitFeedback(
  assignmentId: string,
  body: { client_rating?: number; client_feedback?: string }
): Promise<AssignmentState> {
  return apiFetch<AssignmentState>(`/workouts/assignments/${assignmentId}/feedback`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

export async function overrideProgress(
  assignmentId: string,
  body: { current_week?: number; current_day?: number; status?: string }
): Promise<AssignmentState> {
  return apiFetch<AssignmentState>(`/workouts/assignments/${assignmentId}/progress`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}
