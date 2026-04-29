import type { ProgressionPattern, IntensityLevel, RepRange } from "./types";

/**
 * Build a choose() expression for linear RPE progression across N weeks.
 * Ramps from baseRpe to 9.
 */
export function linearRpeExpr(baseRpe: number, weeks: number): string {
  const step = (9 - baseRpe) / Math.max(weeks - 1, 1);
  const values = Array.from({ length: weeks }, (_, i) =>
    Math.round((baseRpe + step * i) * 2) / 2
  );
  return `choose(ctx.week,[${values.join(",")}])`;
}

/**
 * Build a choose() expression for undulating reps (alternating high/low).
 */
export function undulatingRepsExpr(repsMin: number, repsMax: number, weeks: number): string {
  const values = Array.from({ length: weeks }, (_, i) =>
    i % 2 === 0 ? repsMax : repsMin
  );
  return `choose(ctx.week,[${values.join(",")}])`;
}

/**
 * Return a fixed literal expression string (e.g. "5" or "'moderate'").
 */
export function fixedExpr(value: number | string): string {
  if (typeof value === "string") return `'${value}'`;
  return String(value);
}

/**
 * Map a friendly RepRange to {reps_min, reps_max}.
 */
export function repRangeToBounds(
  range: RepRange,
  customMin?: number,
  customMax?: number
): { repsMin: number; repsMax: number } {
  switch (range) {
    case "light":
      return { repsMin: 12, repsMax: 15 };
    case "moderate":
      return { repsMin: 6, repsMax: 10 };
    case "heavy":
      return { repsMin: 3, repsMax: 5 };
    case "custom":
      return { repsMin: customMin ?? 8, repsMax: customMax ?? 12 };
  }
}

/**
 * Map a friendly IntensityLevel to RPE and RIR values.
 */
export function intensityToRpeRir(level: IntensityLevel): { rpe: number; rir: number } {
  switch (level) {
    case "easy":
      return { rpe: 6, rir: 4 };
    case "moderate":
      return { rpe: 7.5, rir: 2 };
    case "hard":
      return { rpe: 9, rir: 1 };
  }
}

/**
 * Build output_mapping for a reps_range_rir prescription.
 */
export function buildRepsRangeOutputMapping(opts: {
  sets: number;
  repRange: RepRange;
  customRepsMin?: number;
  customRepsMax?: number;
  intensityLevel: IntensityLevel;
  progression: ProgressionPattern;
  weeks: number;
}): Record<string, string> {
  const { repsMin, repsMax } = repRangeToBounds(opts.repRange, opts.customRepsMin, opts.customRepsMax);
  const { rir } = intensityToRpeRir(opts.intensityLevel);

  let repsMinExpr: string;
  let repsMaxExpr: string;

  if (opts.progression === "undulating") {
    repsMinExpr = undulatingRepsExpr(repsMin, Math.floor(repsMin * 1.3), opts.weeks);
    repsMaxExpr = undulatingRepsExpr(repsMax, Math.floor(repsMax * 1.3), opts.weeks);
  } else {
    repsMinExpr = fixedExpr(repsMin);
    repsMaxExpr = fixedExpr(repsMax);
  }

  return {
    sets_expr: fixedExpr(opts.sets),
    reps_min_expr: repsMinExpr,
    reps_max_expr: repsMaxExpr,
    target_rir_expr: fixedExpr(rir),
  };
}

/**
 * Build output_mapping for a top_set_plus_backoff prescription.
 */
export function buildTopSetOutputMapping(opts: {
  sets: number;
  repRange: RepRange;
  customRepsMin?: number;
  customRepsMax?: number;
  intensityLevel: IntensityLevel;
  progression: ProgressionPattern;
  weeks: number;
}): Record<string, string> {
  const { repsMin, repsMax } = repRangeToBounds(opts.repRange, opts.customRepsMin, opts.customRepsMax);
  const { rpe } = intensityToRpeRir(opts.intensityLevel);
  const midReps = Math.round((repsMin + repsMax) / 2);

  let rpeExpr: string;
  let repsExpr: string;

  if (opts.progression === "linear") {
    rpeExpr = linearRpeExpr(rpe - 1.5, opts.weeks);
    repsExpr = fixedExpr(midReps);
  } else if (opts.progression === "undulating") {
    rpeExpr = undulatingRepsExpr(rpe - 1, rpe, opts.weeks);
    repsExpr = undulatingRepsExpr(repsMin, repsMax, opts.weeks);
  } else {
    rpeExpr = fixedExpr(rpe);
    repsExpr = fixedExpr(midReps);
  }

  return {
    sets_expr: fixedExpr(opts.sets),
    reps_expr: repsExpr,
    target_rpe_expr: rpeExpr,
    backoff_sets_expr: fixedExpr(Math.max(1, opts.sets - 1)),
    backoff_reps_expr: repsExpr,
    backoff_load_factor_expr: "0.85",
  };
}

/**
 * Build output_mapping for a steady_state (conditioning) prescription.
 */
export function buildSteadyStateOutputMapping(opts: {
  sets: number;
}): Record<string, string> {
  return {
    duration_minutes_expr: String(opts.sets * 5),
    intensity_target_expr: "'moderate'",
    notes_expr: "'Conditioning block'",
  };
}
