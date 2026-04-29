import { expect, test } from "@playwright/test";

test.describe("Plan Generation API", () => {
  const apiUrl =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  test("generates a strength plan via API", async ({ request }) => {
    const resp = await request.post(`${apiUrl}/api/v1/generate`, {
      data: {
        program_id: "strength_ul_4w_v1",
        program_version: "1.0.0",
        weeks: 4,
        days_per_week: 4,
        athlete: {
          level: "intermediate",
          time_budget_minutes: 90,
          equipment: [
            "barbell",
            "rack",
            "bench",
            "dumbbells",
            "cable",
            "machine",
            "pullup_bar",
          ],
          e1rm: {
            squat: 160.0,
            bench: 115.0,
            deadlift: 190.0,
            ohp: 70.0,
          },
        },
        rules: {
          rounding_profile: "plate_2p5kg",
          volume_metric: "hard_sets_weighted",
          allow_optional_ohp: true,
          hard_set_rule: "RIR_LE_4",
          main_method: "HYBRID",
          accessory_rir_target: 2,
        },
      },
    });

    expect(resp.ok()).toBeTruthy();
    const plan = await resp.json();
    expect(plan.program_id).toBe("strength_ul_4w_v1");
    expect(plan.weeks).toHaveLength(4);
    expect(plan.weeks[0].sessions).toHaveLength(4);
  });

  test("generates a conditioning plan via API", async ({
    request,
  }) => {
    const resp = await request.post(`${apiUrl}/api/v1/generate`, {
      data: {
        program_id: "conditioning_4w_v1",
        program_version: "1.0.0",
        weeks: 4,
        days_per_week: 4,
        athlete: {
          level: "intermediate",
          time_budget_minutes: 60,
          modality: "run",
          equipment: [],
        },
        conditioning: {
          method: "HR_ZONES",
          hr_zone_formula: "KARVONEN_HRR",
          hr_max: 190,
          hr_rest: 55,
        },
      },
    });

    expect(resp.ok()).toBeTruthy();
    const plan = await resp.json();
    expect(plan.program_id).toBe("conditioning_4w_v1");
    expect(plan.weeks).toHaveLength(4);
  });

  test("returns 404 for unknown program", async ({ request }) => {
    const resp = await request.post(`${apiUrl}/api/v1/generate`, {
      data: {
        program_id: "nonexistent",
        program_version: "1.0.0",
        weeks: 4,
        days_per_week: 4,
        athlete: {
          level: "intermediate",
          time_budget_minutes: 60,
          equipment: [],
        },
      },
    });

    expect(resp.status()).toBe(404);
  });

  test("returns 422 for invalid request", async ({ request }) => {
    const resp = await request.post(`${apiUrl}/api/v1/generate`, {
      data: {},
    });

    expect(resp.status()).toBe(422);
  });
});
