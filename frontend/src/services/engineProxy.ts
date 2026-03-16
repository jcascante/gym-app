import { apiFetch } from './api';
import type {
  EngineProgramSummary,
  EngineProgramDefinition,
  GeneratedPlan,
  AlternativesResponse,
} from '../types/engine';

export async function listProgramDefinitions(): Promise<EngineProgramSummary[]> {
  return apiFetch<EngineProgramSummary[]>('/engine/program-definitions');
}

export async function getProgramDefinition(programId: string): Promise<EngineProgramDefinition> {
  return apiFetch<EngineProgramDefinition>(`/engine/program-definitions/${programId}`);
}

export async function generatePlan(payload: Record<string, unknown>): Promise<GeneratedPlan> {
  return apiFetch<GeneratedPlan>('/engine/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getAlternatives(payload: {
  exercise_id: string;
  athlete_equipment: string[];
  restrictions?: string[];
  exclude_ids?: string[];
  limit?: number;
}): Promise<AlternativesResponse> {
  return apiFetch<AlternativesResponse>('/engine/exercises/alternatives', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function applyOverrides(payload: {
  plan: GeneratedPlan;
  overrides: Array<{ block_id: string; new_exercise_id: string }>;
}): Promise<{ plan: GeneratedPlan; applied: unknown[]; rejected: unknown[] }> {
  return apiFetch('/engine/plans/apply-overrides', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
