/**
 * Workout API service
 *
 * Handles workout logging and tracking operations
 */

import { apiFetch } from './api';

// ============================================================================
// Types
// ============================================================================

export interface WorkoutStats {
  total_workouts: number;
  completed_workouts: number;
  skipped_workouts: number;
  last_workout_date: string | null;
}

export interface WorkoutLog {
  id: string;
  client_id: string;
  coach_id?: string;
  program_id: string;
  assignment_id: string;
  status: 'completed' | 'skipped' | 'scheduled';
  workout_date: string;
  duration_minutes?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface RecentWorkout {
  id: string;
  workout_date: string;
  status: 'completed' | 'skipped' | 'scheduled';
  duration_minutes?: string;
  notes?: string;
  program_name?: string;
  assignment_name?: string;
}

export interface WorkoutHistoryResponse {
  total: number;
  count: number;
  offset: number;
  limit: number;
  workouts: WorkoutLog[];
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get workout statistics for the current user
 *
 * @returns Promise with workout statistics
 */
export async function getWorkoutStats(): Promise<WorkoutStats> {
  return apiFetch<WorkoutStats>('/workouts/stats');
}

/**
 * Get recent workouts for the current user
 *
 * @param days Number of days to look back (1-90)
 * @param limit Maximum number of results (1-100)
 * @returns Promise with recent workouts
 */
export async function getRecentWorkouts(
  days: number = 7,
  limit: number = 10
): Promise<RecentWorkout[]> {
  return apiFetch<RecentWorkout[]>(
    `/workouts/recent?days=${days}&limit=${limit}`
  );
}

/**
 * Get workout history for the current user
 *
 * @param limit Maximum number of results
 * @param offset Pagination offset
 * @param status Optional status filter
 * @returns Promise with workout history
 */
export async function getWorkoutHistory(
  limit: number = 20,
  offset: number = 0,
  status?: 'completed' | 'skipped' | 'scheduled'
): Promise<WorkoutHistoryResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
    ...(status && { status }),
  });
  return apiFetch<WorkoutHistoryResponse>(`/workouts?${params}`);
}

/**
 * Get details for a specific workout
 *
 * @param workoutId Workout ID
 * @returns Promise with workout details
 */
export async function getWorkout(workoutId: string): Promise<WorkoutLog> {
  return apiFetch<WorkoutLog>(`/workouts/${workoutId}`);
}

/**
 * Log a new workout
 *
 * @param assignmentId Program assignment ID
 * @param status Workout status
 * @param durationMinutes Duration in minutes (optional)
 * @param notes Workout notes (optional)
 * @param workoutDate Workout date (optional, defaults to now)
 * @returns Promise with created workout
 */
export async function createWorkout(
  assignmentId: string,
  status: 'completed' | 'skipped' | 'scheduled' = 'completed',
  durationMinutes?: string,
  notes?: string,
  workoutDate?: string
): Promise<WorkoutLog> {
  return apiFetch<WorkoutLog>('/workouts', {
    method: 'POST',
    body: JSON.stringify({
      assignment_id: assignmentId,
      status,
      duration_minutes: durationMinutes,
      notes,
      workout_date: workoutDate,
    }),
  });
}

/**
 * Update a workout
 *
 * @param workoutId Workout ID
 * @param status New status (optional)
 * @param durationMinutes New duration (optional)
 * @param notes New notes (optional)
 * @returns Promise with updated workout
 */
export async function updateWorkout(
  workoutId: string,
  status?: 'completed' | 'skipped' | 'scheduled',
  durationMinutes?: string,
  notes?: string
): Promise<WorkoutLog> {
  return apiFetch<WorkoutLog>(`/workouts/${workoutId}`, {
    method: 'PUT',
    body: JSON.stringify({
      status,
      duration_minutes: durationMinutes,
      notes,
    }),
  });
}

/**
 * Delete a workout
 *
 * @param workoutId Workout ID
 * @returns Promise that resolves when deleted
 */
export async function deleteWorkout(workoutId: string): Promise<void> {
  await apiFetch<void>(`/workouts/${workoutId}`, {
    method: 'DELETE',
  });
}


/**
 * Get all workouts for a specific program assignment
 *
 * @param assignmentId Program assignment ID
 */
export async function getAssignmentWorkouts(assignmentId: string) {
  return apiFetch<WorkoutLog[]>(`/workouts/assignments/${assignmentId}/workouts`);
}
