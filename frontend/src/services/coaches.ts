/**
 * Coach API service
 *
 * Handles coach-specific operations like dashboard statistics
 */

import { apiFetch } from './api';

// ============================================================================
// Types
// ============================================================================

export interface CoachStats {
  total_clients: number;
  active_clients: number;
  total_programs: number;
  active_programs: number;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get dashboard statistics for the current coach
 *
 * @returns Promise with coach statistics
 */
export async function getCoachStats(): Promise<CoachStats> {
  return apiFetch<CoachStats>('/coaches/me/stats');
}
