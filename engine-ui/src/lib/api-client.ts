import type {
  ApplyOverridesRequest,
  ApplyOverridesResponse,
  ExerciseAlternativesRequest,
  ExerciseAlternativesResponse,
  ExerciseLibraryEntry,
  GeneratedPlan,
  PlanRequest,
  ProgramDefinitionSummary,
  ProgramDefinitionFull,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchJSON<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function getExerciseLibrary() {
  return fetchJSON<{ version: string; exercises: ExerciseLibraryEntry[] }>(
    "/api/v1/exercise-library"
  );
}

export async function listProgramDefinitions() {
  return fetchJSON<ProgramDefinitionSummary[]>(
    "/api/v1/program-definitions"
  );
}

export async function getProgramDefinition(programId: string) {
  return fetchJSON<ProgramDefinitionFull>(
    `/api/v1/program-definitions/${programId}`
  );
}

export async function generatePlan(
  request: PlanRequest
): Promise<GeneratedPlan> {
  return fetchJSON<GeneratedPlan>("/api/v1/generate", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getExerciseAlternatives(
  request: ExerciseAlternativesRequest
): Promise<ExerciseAlternativesResponse> {
  return fetchJSON<ExerciseAlternativesResponse>("/api/v1/exercises/alternatives", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function applyOverrides(
  request: ApplyOverridesRequest
): Promise<ApplyOverridesResponse> {
  return fetchJSON<ApplyOverridesResponse>("/api/v1/plans/apply-overrides", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function validateDefinition(
  definition: Record<string, unknown>
): Promise<{ valid: boolean; errors: string[] }> {
  return fetchJSON<{ valid: boolean; errors: string[] }>(
    "/api/v1/validate-definition",
    {
      method: "POST",
      body: JSON.stringify(definition),
    }
  );
}
