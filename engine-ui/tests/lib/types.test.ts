import { describe, expect, it } from "vitest";
import {
  isConditioningPrescription,
  isIntervalPrescription,
  isRepsRangePrescription,
  isStrengthPrescription,
} from "@/lib/types";

describe("type guards", () => {
  it("detects strength prescription", () => {
    const rx = {
      top_set: { sets: 1, reps: 5, target_rpe: 7, load_kg: 120 },
      backoff: [{ sets: 3, reps: 5, load_kg: 107.5 }],
    };
    expect(isStrengthPrescription(rx)).toBe(true);
    expect(isRepsRangePrescription(rx)).toBe(false);
    expect(isConditioningPrescription(rx)).toBe(false);
    expect(isIntervalPrescription(rx)).toBe(false);
  });

  it("detects reps range prescription", () => {
    const rx = {
      sets: 3,
      reps_range: [8, 12] as [number, number],
      target_rir: 2,
    };
    expect(isRepsRangePrescription(rx)).toBe(true);
    expect(isStrengthPrescription(rx)).toBe(false);
  });

  it("detects conditioning prescription", () => {
    const rx = {
      duration_minutes: 35,
      intensity: { method: "HR_ZONES", target: "z(2)" },
    };
    expect(isConditioningPrescription(rx)).toBe(true);
    expect(isIntervalPrescription(rx)).toBe(false);
  });

  it("detects interval prescription", () => {
    const rx = {
      warmup_minutes: 10,
      work: {
        intervals: 4,
        minutes_each: 4,
        intensity: { method: "HR_ZONES", target: "thr()" },
      },
      cooldown_minutes: 8,
    };
    expect(isIntervalPrescription(rx)).toBe(true);
    expect(isConditioningPrescription(rx)).toBe(false);
  });
});
