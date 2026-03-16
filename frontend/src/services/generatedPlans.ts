import { apiFetch } from './api';
import type { SavedPlanSummary, SavedPlanDetail, SavePlanRequest } from '../types/engine';

export async function savePlan(data: SavePlanRequest): Promise<SavedPlanDetail> {
  return apiFetch<SavedPlanDetail>('/me/plans', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function listMyGeneratedPlans(): Promise<SavedPlanSummary[]> {
  return apiFetch<SavedPlanSummary[]>('/me/plans');
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
