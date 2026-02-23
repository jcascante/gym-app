/**
 * Admin API service
 *
 * Handles admin dashboard operations and system management
 */

import { apiFetch } from './api';

// ============================================================================
// Types
// ============================================================================

export interface AdminStats {
  total_users: number;
  active_coaches: number;
  active_clients: number;
  total_programs: number;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get admin dashboard statistics
 *
 * **Authorization**: SUBSCRIPTION_ADMIN or APPLICATION_SUPPORT only
 *
 * @returns Promise with admin statistics
 */
export async function getAdminStats(): Promise<AdminStats> {
  return apiFetch<AdminStats>('/coaches/me/admin/stats');
}
