import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import {
  ApiError,
  generatePlan,
  getExerciseLibrary,
  listProgramDefinitions,
} from "@/lib/api-client";

const server = setupServer(
  http.get("http://localhost:8000/api/v1/exercise-library", () => {
    return HttpResponse.json({
      version: "1.0.0",
      exercises: [{ id: "squat", name: "Squat" }],
    });
  }),

  http.get("http://localhost:8000/api/v1/program-definitions", () => {
    return HttpResponse.json([
      {
        program_id: "strength_ul_4w_v1",
        version: "1.0.0",
        name: "UL Strength",
        description: null,
      },
    ]);
  }),

  http.post("http://localhost:8000/api/v1/generate", () => {
    return HttpResponse.json({
      program_id: "strength_ul_4w_v1",
      program_version: "1.0.0",
      generated_at: "2026-02-23T00:00:00Z",
      inputs_echo: {},
      weeks: [],
      warnings: [],
      repairs: [],
    });
  })
);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("getExerciseLibrary", () => {
  it("fetches library", async () => {
    const data = await getExerciseLibrary();
    expect(data.version).toBe("1.0.0");
    expect(data.exercises).toHaveLength(1);
  });
});

describe("listProgramDefinitions", () => {
  it("fetches definitions list", async () => {
    const data = await listProgramDefinitions();
    expect(data).toHaveLength(1);
    expect(data[0].program_id).toBe("strength_ul_4w_v1");
  });
});

describe("generatePlan", () => {
  it("sends POST and returns plan", async () => {
    const plan = await generatePlan({
      program_id: "strength_ul_4w_v1",
      program_version: "1.0.0",
      weeks: 4,
      days_per_week: 4,
      athlete: {
        level: "intermediate",
        time_budget_minutes: 90,
        equipment: ["barbell"],
      },
    });
    expect(plan.program_id).toBe("strength_ul_4w_v1");
  });

  it("throws ApiError on 404", async () => {
    server.use(
      http.post("http://localhost:8000/api/v1/generate", () => {
        return HttpResponse.json(
          { detail: "Not found" },
          { status: 404 }
        );
      })
    );

    await expect(
      generatePlan({
        program_id: "nonexistent",
        program_version: "1.0.0",
        weeks: 4,
        days_per_week: 4,
        athlete: {
          level: "intermediate",
          time_budget_minutes: 60,
          equipment: [],
        },
      })
    ).rejects.toThrow(ApiError);
  });
});
