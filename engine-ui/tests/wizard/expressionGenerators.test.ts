import { describe, it, expect } from "vitest";
import {
  linearRpeExpr,
  undulatingRepsExpr,
  fixedExpr,
  repRangeToBounds,
  intensityToRpeRir,
  buildRepsRangeOutputMapping,
  buildTopSetOutputMapping,
  buildSteadyStateOutputMapping,
} from "@/lib/wizard/expressionGenerators";

describe("fixedExpr", () => {
  it("returns numeric string for numbers", () => {
    expect(fixedExpr(5)).toBe("5");
    expect(fixedExpr(7.5)).toBe("7.5");
  });
  it("wraps strings in single quotes", () => {
    expect(fixedExpr("moderate")).toBe("'moderate'");
  });
});

describe("linearRpeExpr", () => {
  it("generates choose() expression ramping from baseRpe to 9", () => {
    const expr = linearRpeExpr(7.5, 4);
    expect(expr).toMatch(/^choose\(ctx\.week,\[/);
    expect(expr).toContain("7.5");
    // Last value should be 9
    const values = expr.match(/\[(.+)\]/)?.[1].split(",").map(Number);
    expect(values).toBeDefined();
    expect(values![values!.length - 1]).toBe(9);
  });
  it("produces correct number of values", () => {
    const expr = linearRpeExpr(6, 4);
    const values = expr.match(/\[(.+)\]/)?.[1].split(",");
    expect(values).toHaveLength(4);
  });
  it("returns single value for 1 week", () => {
    const expr = linearRpeExpr(9, 1);
    expect(expr).toBe("choose(ctx.week,[9])");
  });
});

describe("undulatingRepsExpr", () => {
  it("alternates high/low reps for even/odd indices", () => {
    const expr = undulatingRepsExpr(6, 10, 4);
    expect(expr).toMatch(/^choose\(ctx\.week,\[/);
    const values = expr.match(/\[(.+)\]/)?.[1].split(",").map(Number);
    expect(values![0]).toBe(10); // week index 0 → high
    expect(values![1]).toBe(6);  // week index 1 → low
    expect(values![2]).toBe(10);
    expect(values![3]).toBe(6);
  });
});

describe("repRangeToBounds", () => {
  it("maps light to 12-15", () => {
    expect(repRangeToBounds("light")).toEqual({ repsMin: 12, repsMax: 15 });
  });
  it("maps moderate to 6-10", () => {
    expect(repRangeToBounds("moderate")).toEqual({ repsMin: 6, repsMax: 10 });
  });
  it("maps heavy to 3-5", () => {
    expect(repRangeToBounds("heavy")).toEqual({ repsMin: 3, repsMax: 5 });
  });
  it("uses custom values", () => {
    expect(repRangeToBounds("custom", 8, 12)).toEqual({ repsMin: 8, repsMax: 12 });
  });
  it("uses defaults for custom with no values", () => {
    const result = repRangeToBounds("custom");
    expect(result.repsMin).toBeGreaterThan(0);
    expect(result.repsMax).toBeGreaterThan(result.repsMin);
  });
});

describe("intensityToRpeRir", () => {
  it("easy → rpe=6, rir=4", () => {
    expect(intensityToRpeRir("easy")).toEqual({ rpe: 6, rir: 4 });
  });
  it("moderate → rpe=7.5, rir=2", () => {
    expect(intensityToRpeRir("moderate")).toEqual({ rpe: 7.5, rir: 2 });
  });
  it("hard → rpe=9, rir=1", () => {
    expect(intensityToRpeRir("hard")).toEqual({ rpe: 9, rir: 1 });
  });
});

describe("buildRepsRangeOutputMapping", () => {
  it("returns required keys", () => {
    const mapping = buildRepsRangeOutputMapping({
      sets: 3,
      repRange: "moderate",
      intensityLevel: "moderate",
      progression: "fixed",
      weeks: 4,
    });
    expect(mapping).toHaveProperty("sets_expr");
    expect(mapping).toHaveProperty("reps_min_expr");
    expect(mapping).toHaveProperty("reps_max_expr");
    expect(mapping).toHaveProperty("target_rir_expr");
  });
  it("uses fixed expressions for fixed progression", () => {
    const mapping = buildRepsRangeOutputMapping({
      sets: 3,
      repRange: "moderate",
      intensityLevel: "moderate",
      progression: "fixed",
      weeks: 4,
    });
    expect(mapping.reps_min_expr).toBe("6");
    expect(mapping.reps_max_expr).toBe("10");
    expect(mapping.target_rir_expr).toBe("2");
  });
  it("uses choose() for undulating progression", () => {
    const mapping = buildRepsRangeOutputMapping({
      sets: 3,
      repRange: "moderate",
      intensityLevel: "moderate",
      progression: "undulating",
      weeks: 4,
    });
    expect(mapping.reps_min_expr).toContain("choose(ctx.week");
    expect(mapping.reps_max_expr).toContain("choose(ctx.week");
  });
});

describe("buildTopSetOutputMapping", () => {
  it("returns required keys", () => {
    const mapping = buildTopSetOutputMapping({
      sets: 4,
      repRange: "heavy",
      intensityLevel: "hard",
      progression: "linear",
      weeks: 4,
    });
    expect(mapping).toHaveProperty("sets_expr");
    expect(mapping).toHaveProperty("reps_expr");
    expect(mapping).toHaveProperty("target_rpe_expr");
    expect(mapping).toHaveProperty("backoff_sets_expr");
    expect(mapping).toHaveProperty("backoff_reps_expr");
    expect(mapping).toHaveProperty("backoff_load_factor_expr", "0.85");
  });
  it("linear progression uses choose() for RPE", () => {
    const mapping = buildTopSetOutputMapping({
      sets: 4,
      repRange: "heavy",
      intensityLevel: "hard",
      progression: "linear",
      weeks: 4,
    });
    expect(mapping.target_rpe_expr).toContain("choose(ctx.week");
  });
  it("fixed progression uses literal RPE", () => {
    const mapping = buildTopSetOutputMapping({
      sets: 4,
      repRange: "heavy",
      intensityLevel: "hard",
      progression: "fixed",
      weeks: 4,
    });
    expect(mapping.target_rpe_expr).not.toContain("choose");
  });
});

describe("buildSteadyStateOutputMapping", () => {
  it("returns duration_minutes_expr as sets * 5", () => {
    const mapping = buildSteadyStateOutputMapping({ sets: 3 });
    expect(mapping.duration_minutes_expr).toBe("15");
  });
  it("includes intensity and notes", () => {
    const mapping = buildSteadyStateOutputMapping({ sets: 3 });
    expect(mapping).toHaveProperty("intensity_target_expr");
    expect(mapping).toHaveProperty("notes_expr");
  });
});
