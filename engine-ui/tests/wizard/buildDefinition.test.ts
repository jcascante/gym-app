import { describe, it, expect } from "vitest";
import { buildDefinition, validateDefinitionStructure } from "@/lib/wizard/buildDefinition";
import type { WizardState } from "@/lib/wizard/types";

const baseState: WizardState = {
  currentStep: 5,
  step1: {
    name: "My Strength Program",
    description: "Test program",
    programType: "strength",
    durationWeeks: 4,
    frequencyDays: 3,
  },
  step2: {
    activeDays: [
      { dayIndex: 0, sessionType: "upper_body" },
      { dayIndex: 2, sessionType: "lower_body" },
      { dayIndex: 4, sessionType: "full_body" },
    ],
  },
  step3: {
    sessions: [
      {
        dayIndex: 0,
        sessionType: "upper_body",
        blocks: [
          { id: "s0_b001", blockType: "main_lift", exerciseCategory: "horizontal_push" },
          { id: "s0_b002", blockType: "accessory", exerciseCategory: "horizontal_pull" },
        ],
      },
      {
        dayIndex: 2,
        sessionType: "lower_body",
        blocks: [
          { id: "s2_b001", blockType: "main_lift", exerciseCategory: "squat" },
        ],
      },
      {
        dayIndex: 4,
        sessionType: "full_body",
        blocks: [
          { id: "s4_b001", blockType: "conditioning", exerciseCategory: "conditioning" },
        ],
      },
    ],
  },
  step4: {
    prescriptions: [
      {
        blockId: "s0_b001",
        trainingStyle: "top_set_plus_backoff",
        sets: 4,
        repRange: "heavy",
        intensityLevel: "hard",
        progression: "linear",
      },
      {
        blockId: "s0_b002",
        trainingStyle: "reps_range_rir",
        sets: 3,
        repRange: "moderate",
        intensityLevel: "moderate",
        progression: "fixed",
      },
      {
        blockId: "s2_b001",
        trainingStyle: "top_set_plus_backoff",
        sets: 4,
        repRange: "heavy",
        intensityLevel: "hard",
        progression: "linear",
      },
      {
        blockId: "s4_b001",
        trainingStyle: "steady_state",
        sets: 3,
        repRange: "moderate",
        intensityLevel: "moderate",
        progression: "fixed",
      },
    ],
  },
};

describe("buildDefinition", () => {
  it("returns an object with all required top-level fields", () => {
    const def = buildDefinition(baseState);
    expect(def).toHaveProperty("program_id");
    expect(def).toHaveProperty("version", "1.0.0");
    expect(def).toHaveProperty("name", "My Strength Program");
    expect(def).toHaveProperty("description", "Test program");
    expect(def).toHaveProperty("parameter_spec");
    expect(def).toHaveProperty("template");
    expect(def).toHaveProperty("prescriptions");
    expect(def).toHaveProperty("rules");
    expect(def).toHaveProperty("validation");
  });

  it("slugifies the name for program_id", () => {
    const def = buildDefinition(baseState);
    expect(def.program_id).toBe("my_strength_program_v1");
  });

  it("sets weeks and days_per_week to fixed range from wizard", () => {
    const def = buildDefinition(baseState);
    const template = def.template as Record<string, unknown>;
    expect(template.weeks).toEqual({ min: 4, max: 4 });
    expect(template.days_per_week).toEqual({ min: 3, max: 3 });
  });

  it("converts dayIndex to 1-based day_index in sessions", () => {
    const def = buildDefinition(baseState);
    const template = def.template as Record<string, unknown>;
    const sessions = template.sessions as Array<Record<string, unknown>>;
    expect(sessions[0].day_index).toBe(1); // dayIndex 0 → day_index 1
    expect(sessions[1].day_index).toBe(3); // dayIndex 2 → day_index 3
    expect(sessions[2].day_index).toBe(5); // dayIndex 4 → day_index 5
  });

  it("creates a prescription_ref for each block matching rx_ prefix", () => {
    const def = buildDefinition(baseState);
    const template = def.template as Record<string, unknown>;
    const sessions = template.sessions as Array<Record<string, unknown>>;
    const firstSession = sessions[0];
    const blocks = firstSession.blocks as Array<Record<string, unknown>>;
    expect(blocks[0].prescription_ref).toBe("rx_s0_b001");
    expect(blocks[1].prescription_ref).toBe("rx_s0_b002");
  });

  it("generates a prescriptions entry for every block", () => {
    const def = buildDefinition(baseState);
    const prescriptions = def.prescriptions as Record<string, unknown>;
    expect(prescriptions).toHaveProperty("rx_s0_b001");
    expect(prescriptions).toHaveProperty("rx_s0_b002");
    expect(prescriptions).toHaveProperty("rx_s2_b001");
    expect(prescriptions).toHaveProperty("rx_s4_b001");
  });

  it("sets correct mode for each block type", () => {
    const def = buildDefinition(baseState);
    const prescriptions = def.prescriptions as Record<string, Record<string, unknown>>;
    expect(prescriptions["rx_s0_b001"].mode).toBe("top_set_plus_backoff");
    expect(prescriptions["rx_s0_b002"].mode).toBe("reps_range_rir");
    expect(prescriptions["rx_s4_b001"].mode).toBe("steady_state");
  });

  it("uses correct exercise tags for categories", () => {
    const def = buildDefinition(baseState);
    const template = def.template as Record<string, unknown>;
    const sessions = template.sessions as Array<Record<string, unknown>>;
    const blocks = sessions[0].blocks as Array<Record<string, unknown>>;
    const selector = blocks[0].exercise_selector as Record<string, unknown>;
    expect(selector.include_tags).toEqual(["horizontal_push"]);
  });

  it("uses hypertrophy preset for hypertrophy type", () => {
    const state = { ...baseState, step1: { ...baseState.step1, programType: "hypertrophy" as const } };
    const def = buildDefinition(state);
    const validation = def.validation as Record<string, unknown>;
    const hard = validation.hard as Record<string, unknown>;
    const maxVol = hard.max_weekly_volume_by_key as Record<string, unknown>;
    expect(String(maxVol.limit_expr)).toContain("novice");
  });

  it("uses conditioning preset for conditioning type", () => {
    const state = { ...baseState, step1: { ...baseState.step1, programType: "conditioning" as const } };
    const def = buildDefinition(state);
    const paramSpec = def.parameter_spec as Record<string, unknown>;
    const fields = paramSpec.fields as Array<Record<string, unknown>>;
    const hasConditioningMethod = fields.some((f) => f.key === "conditioning.method");
    expect(hasConditioningMethod).toBe(true);
  });

  it("steady_state prescription has duration_minutes_expr", () => {
    const def = buildDefinition(baseState);
    const prescriptions = def.prescriptions as Record<string, Record<string, unknown>>;
    const rx = prescriptions["rx_s4_b001"] as Record<string, unknown>;
    const mapping = rx.output_mapping as Record<string, string>;
    expect(mapping).toHaveProperty("duration_minutes_expr");
  });
});

describe("validateDefinitionStructure", () => {
  it("returns empty array for valid definition", () => {
    const def = buildDefinition(baseState);
    expect(validateDefinitionStructure(def)).toEqual([]);
  });

  it("reports missing required fields", () => {
    const errors = validateDefinitionStructure({ program_id: "test" });
    expect(errors.length).toBeGreaterThan(0);
    expect(errors.some((e) => e.includes("version"))).toBe(true);
  });

  it("reports day_index out of range", () => {
    const def = buildDefinition(baseState);
    const template = def.template as Record<string, unknown>;
    const sessions = (template.sessions as Array<Record<string, unknown>>).map((s, i) =>
      i === 0 ? { ...s, day_index: 0 } : s
    );
    const badDef = { ...def, template: { ...template, sessions } };
    const errors = validateDefinitionStructure(badDef);
    expect(errors.some((e) => e.includes("day_index"))).toBe(true);
  });

  it("reports missing prescription_ref", () => {
    const def = buildDefinition(baseState);
    // Remove a prescription to trigger the error
    const prescriptions = { ...(def.prescriptions as Record<string, unknown>) };
    delete prescriptions["rx_s0_b001"];
    const badDef = { ...def, prescriptions };
    const errors = validateDefinitionStructure(badDef);
    expect(errors.some((e) => e.includes("rx_s0_b001"))).toBe(true);
  });
});
