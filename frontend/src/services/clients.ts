/**
 * Client management API service
 *
 * Provides functions for coaches to manage their assigned clients,
 * including creating, listing, viewing, and updating client information.
 */

import { apiFetch } from './api';

// ============================================================================
// Types
// ============================================================================

export interface CreateClientRequest {
  email: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  send_welcome_email?: boolean;
}

export interface CreateClientResponse {
  client_id: string;
  email: string;
  name: string;
  is_new: boolean;
  profile_complete: boolean;
  already_assigned: boolean;
  temporary_password?: string;
}

export interface ClientSummary {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  name: string;
  profile_photo?: string;
  active_programs: number;
  last_workout?: string;  // ISO datetime string
  status: 'active' | 'inactive' | 'new';
  profile_complete: boolean;
  has_one_rep_maxes: boolean;
  assigned_at: string;  // ISO datetime string
}

export interface ClientListResponse {
  clients: ClientSummary[];
  total: number;
}

export interface OneRepMax {
  weight: number;
  unit: 'lbs' | 'kg';
  tested_date: string;  // ISO date string
  verified: boolean;
}

export interface ClientTrainingExperience {
  overall_experience_level?: 'beginner' | 'novice' | 'intermediate' | 'advanced' | 'elite';
  years_training?: number;
  strength_training_experience?: string;
  one_rep_maxes?: Record<string, OneRepMax>;
  current_training_frequency?: number;
}

export interface ClientInjury {
  injury: string;
  injury_date?: string;
  recovery_status: 'fully_recovered' | 'recovering' | 'chronic' | 'requires_modification';
  affected_movements?: string[];
  notes?: string;
}

export interface ClientHealthInfo {
  medical_clearance: boolean;
  clearance_date?: string;
  injuries?: ClientInjury[];
  medical_conditions?: Array<Record<string, any>>;
  medications?: Array<Record<string, any>>;
  allergies?: string[];
}

export interface ClientProfile {
  basic_info?: {
    first_name: string;
    last_name: string;
    date_of_birth?: string;
    gender?: string;
    phone_number?: string;
  };
  anthropometrics?: {
    current_weight?: number;
    current_height?: number;
    weight_unit?: 'lbs' | 'kg';
    height_unit?: 'inches' | 'cm';
    body_fat_percentage?: number;
    goal_weight?: number;
  };
  training_experience?: ClientTrainingExperience;
  fitness_goals?: {
    primary_goal?: string;
    secondary_goals?: string[];
    specific_goals?: string;
    target_date?: string;
    motivation?: string;
  };
  health_info?: ClientHealthInfo;
  training_preferences?: {
    available_days_per_week?: number;
    preferred_training_days?: string[];
    session_duration?: number;
    gym_access?: string;
    available_equipment?: string[];
    preferred_exercises?: string[];
    disliked_exercises?: string[];
  };
  notes?: Record<string, string>;
}

export interface ClientDetailResponse {
  id: string;
  email: string;
  profile?: ClientProfile;
  is_active: boolean;
  assigned_at: string;
  assigned_by: string;
  active_programs: number;
  completed_programs: number;
  total_workouts: number;
  last_workout?: string;
  last_login_at?: string;
  created_at: string;
}

export interface UpdateOneRepMaxRequest {
  exercise_name: string;
  weight: number;
  unit: 'lbs' | 'kg';
  tested_date: string;  // ISO date string
  verified?: boolean;
}

export interface OneRepMaxResponse {
  client_id: string;
  exercise_name: string;
  weight: number;
  unit: 'lbs' | 'kg';
  tested_date: string;
  verified: boolean;
  updated_at: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Create a new client or find existing client by email
 *
 * @param data - Client creation data (email, first_name, last_name, optional phone)
 * @returns Promise with client info and whether they're new or existing
 */
export async function createClient(data: CreateClientRequest): Promise<CreateClientResponse> {
  return apiFetch<CreateClientResponse>('/coaches/me/clients', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Get list of all clients assigned to current coach
 *
 * @param params - Optional query parameters (status filter, search)
 * @returns Promise with list of clients
 */
export async function listMyClients(params?: {
  status?: 'active' | 'inactive' | 'new';
  search?: string;
}): Promise<ClientListResponse> {
  const queryParams = new URLSearchParams();

  if (params?.status) {
    queryParams.append('status_filter', params.status);
  }

  if (params?.search) {
    queryParams.append('search', params.search);
  }

  const queryString = queryParams.toString();
  const endpoint = `/coaches/me/clients${queryString ? `?${queryString}` : ''}`;

  return apiFetch<ClientListResponse>(endpoint);
}

/**
 * Get detailed information about a specific client
 *
 * @param clientId - Client's user ID
 * @returns Promise with full client details
 */
export async function getClientDetail(clientId: string): Promise<ClientDetailResponse> {
  return apiFetch<ClientDetailResponse>(`/coaches/me/clients/${clientId}`);
}

/**
 * Update client profile information
 *
 * @param clientId - Client's user ID
 * @param updates - Partial profile updates
 * @returns Promise with updated client details
 */
export async function updateClientProfile(
  clientId: string,
  updates: Partial<ClientProfile>
): Promise<ClientDetailResponse> {
  return apiFetch<ClientDetailResponse>(`/coaches/me/clients/${clientId}/profile`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  });
}

/**
 * Add or update a client's 1RM for a specific exercise
 *
 * @param clientId - Client's user ID
 * @param data - 1RM data (exercise name, weight, unit, date, verified)
 * @returns Promise with updated 1RM info
 */
export async function updateClientOneRepMax(
  clientId: string,
  data: UpdateOneRepMaxRequest
): Promise<OneRepMaxResponse> {
  return apiFetch<OneRepMaxResponse>(`/coaches/me/clients/${clientId}/one-rep-max`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * Remove client assignment (unassign client from coach)
 *
 * @param clientId - Client's user ID
 * @returns Promise with success message
 */
export async function removeClientAssignment(clientId: string): Promise<{ message: string }> {
  return apiFetch<{ message: string }>(`/coaches/me/clients/${clientId}`, {
    method: 'DELETE',
  });
}

export interface ClientWorkoutEntry {
  id: string;
  status: 'completed' | 'skipped' | 'scheduled';
  workout_date: string;
  duration_minutes: string | null;
  notes: string | null;
  program_name: string | null;
  assignment_id: string;
  created_at: string;
}

export interface ClientWorkoutHistoryResponse {
  client_id: string;
  total: number;
  count: number;
  offset: number;
  limit: number;
  workouts: ClientWorkoutEntry[];
}

/**
 * Get workout history for a client (coach view)
 */
export async function getClientWorkoutHistory(
  clientId: string,
  limit = 50,
  offset = 0
): Promise<ClientWorkoutHistoryResponse> {
  return apiFetch<ClientWorkoutHistoryResponse>(
    `/coaches/me/clients/${clientId}/workouts?limit=${limit}&offset=${offset}`
  );
}
