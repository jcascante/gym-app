import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BlockRow } from "@/components/plan/BlockRow";
import type { PlanBlock } from "@/lib/types";

describe("BlockRow", () => {
  it("renders strength prescription", () => {
    const block: PlanBlock = {
      block_id: "w1d1_main",
      type: "main_lift",
      exercise: { id: "back_squat", name: "Back Squat" },
      prescription: {
        top_set: { sets: 1, reps: 5, target_rpe: 7, load_kg: 120 },
        backoff: [{ sets: 3, reps: 5, load_kg: 107.5 }],
      },
    };
    render(<BlockRow block={block} />);
    expect(screen.getByText("Back Squat")).toBeInTheDocument();
    expect(screen.getByTestId("strength-rx")).toBeInTheDocument();
    expect(screen.getByTestId("strength-rx").textContent).toContain(
      "120 kg"
    );
  });

  it("renders reps range prescription", () => {
    const block: PlanBlock = {
      block_id: "w1d1_acc",
      type: "accessory",
      exercise: { id: "leg_press", name: "Leg Press" },
      prescription: {
        sets: 3,
        reps_range: [10, 15],
        target_rir: 2,
      },
    };
    render(<BlockRow block={block} />);
    expect(screen.getByText("Leg Press")).toBeInTheDocument();
    expect(screen.getByTestId("reps-range-rx").textContent).toContain(
      "3 sets"
    );
    expect(screen.getByTestId("reps-range-rx").textContent).toContain(
      "10-15"
    );
  });

  it("renders conditioning prescription", () => {
    const block: PlanBlock = {
      block_id: "w1d1_z2",
      type: "conditioning_steady",
      exercise: { id: "run_steady", name: "Run (Steady)" },
      prescription: {
        duration_minutes: 35,
        intensity: { method: "HR_ZONES", target: "z(2)" },
      },
    };
    render(<BlockRow block={block} />);
    expect(screen.getByText("Run (Steady)")).toBeInTheDocument();
    expect(
      screen.getByTestId("conditioning-rx").textContent
    ).toContain("35 min");
  });

  it("renders interval prescription", () => {
    const block: PlanBlock = {
      block_id: "w1d2_thr",
      type: "conditioning_intervals",
      exercise: { id: "run_intervals", name: "Run (Intervals)" },
      prescription: {
        warmup_minutes: 10,
        work: {
          intervals: 4,
          minutes_each: 4,
          intensity: { method: "HR_ZONES", target: "thr()" },
        },
        cooldown_minutes: 8,
      },
    };
    render(<BlockRow block={block} />);
    expect(screen.getByText("Run (Intervals)")).toBeInTheDocument();
    expect(screen.getByTestId("interval-rx").textContent).toContain(
      "4×4min"
    );
  });
});
