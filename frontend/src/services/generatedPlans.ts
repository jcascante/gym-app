import { apiFetch } from './api';
import type { SavedPlanSummary, SavedPlanDetail, SavePlanRequest } from '../types/engine';

export interface StartPlanRequest {
  start_date: string;
  assignment_name?: string;
}

export interface StartPlanResponse {
  assignment_id: string;
  program_id: string;
  start_date: string;
  end_date: string;
  status: string;
}

export async function savePlan(data: SavePlanRequest): Promise<SavedPlanDetail> {
  return apiFetch<SavedPlanDetail>('/me/plans', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function listMyGeneratedPlans(unstartedOnly = true): Promise<SavedPlanSummary[]> {
  const qs = unstartedOnly ? '?unstarted_only=true' : '';
  return apiFetch<SavedPlanSummary[]>(`/me/plans${qs}`);
}

export async function getMyGeneratedPlan(planId: string): Promise<SavedPlanDetail> {
  return apiFetch<SavedPlanDetail>(`/me/plans/${planId}`);
}

export async function updateMyGeneratedPlan(
  planId: string,
  data: { name?: string; notes?: string; plan_data?: unknown }
): Promise<SavedPlanDetail> {
  return apiFetch<SavedPlanDetail>(`/me/plans/${planId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteMyGeneratedPlan(planId: string): Promise<void> {
  await apiFetch<{ deleted: boolean }>(`/me/plans/${planId}`, { method: 'DELETE' });
}

export async function startSavedPlan(planId: string, body: StartPlanRequest): Promise<StartPlanResponse> {
  return apiFetch<StartPlanResponse>(`/me/plans/${planId}/start`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}
