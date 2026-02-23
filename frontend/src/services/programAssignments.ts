/**
 * Program Assignment API service
 *
 * Handles assigning programs to clients and tracking progress
 */

import { apiFetch } from './api';

// ============================================================================
// Types
// ============================================================================

export interface ProgramAssignmentSummary {
  assignment_id: string;
  program_id: string;
  program_name: string;
  assignment_name?: string;
  duration_weeks: number;
  days_per_week: number;
  start_date: string;  // ISO date
  end_date?: string;   // ISO date
  actual_completion_date?: string;  // ISO date
  status: 'assigned' | 'in_progress' | 'completed' | 'paused' | 'cancelled';
  program_status: string | null;  // null = old template-linked, 'draft', 'published'
  current_week: number;
  current_day: number;
  progress_percentage: number;
  is_active: boolean;
  assigned_at: string;  // ISO datetime
  assigned_by_name: string;
}

export interface ClientProgramsListResponse {
  client_id: string;
  client_name: string;
  programs: ProgramAssignmentSummary[];
  total: number;
  active_count: number;
  completed_count: number;
}

export interface AssignProgramRequest {
  client_id: string;
  assignment_name?: string;
  start_date?: string;  // ISO date (YYYY-MM-DD)
  notes?: string;
}

export interface AssignProgramResponse {
  assignment_id: string;
  program_id: string;
  program_name: string;
  client_id: string;
  client_name: string;
  assignment_name?: string;
  start_date: string;
  end_date?: string;
  status: string;
  created_at: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get all programs assigned to a specific client
 *
 * @param clientId - Client's user ID
 * @param statusFilter - Optional status filter
 * @returns Promise with list of program assignments
 */
export async function getClientPrograms(
  clientId: string,
  statusFilter?: 'assigned' | 'in_progress' | 'completed' | 'paused' | 'cancelled'
): Promise<ClientProgramsListResponse> {
  const queryParams = new URLSearchParams();

  if (statusFilter) {
    queryParams.append('status_filter', statusFilter);
  }

  const queryString = queryParams.toString();
  const endpoint = `/coaches/me/clients/${clientId}/programs${queryString ? `?${queryString}` : ''}`;

  return apiFetch<ClientProgramsListResponse>(endpoint);
}


/**
 * Get programs assigned to the authenticated client (self)
 *
 * @param statusFilter - Optional status filter
 */
export async function getMyPrograms(
  statusFilter?: 'assigned' | 'in_progress' | 'completed' | 'paused' | 'cancelled'
): Promise<ClientProgramsListResponse> {
  const queryParams = new URLSearchParams();

  if (statusFilter) {
    queryParams.append('status_filter', statusFilter);
  }

  const queryString = queryParams.toString();
  const endpoint = `/users/me/programs${queryString ? `?${queryString}` : ''}`;

  return apiFetch<ClientProgramsListResponse>(endpoint);
}

/**
 * Assign a program to a client
 *
 * @param programId - Program ID to assign
 * @param data - Assignment data (client_id, optional name, start date, notes)
 * @returns Promise with assignment details
 */
export async function assignProgramToClient(
  programId: string,
  data: AssignProgramRequest
): Promise<AssignProgramResponse> {
  return apiFetch<AssignProgramResponse>(`/programs/${programId}/assign`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Remove/delete a program assignment from a client
 *
 * @param clientId - Client's user ID
 * @param assignmentId - Assignment ID to remove
 * @returns Promise with success message
 */
export async function removeProgramAssignment(
  clientId: string,
  assignmentId: string
): Promise<{ message: string }> {
  return apiFetch<{ message: string }>(`/coaches/me/clients/${clientId}/programs/${assignmentId}`, {
    method: 'DELETE',
  });
}
