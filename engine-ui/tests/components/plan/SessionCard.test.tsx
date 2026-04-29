import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SessionCard } from "@/components/plan/SessionCard";
import type { GeneratedSession } from "@/lib/types";

const session: GeneratedSession = {
  day: 1,
  tags: ["lower", "strength_focus"],
  blocks: [
    {
      block_id: "w1d1_main",
      type: "main_lift",
      exercise: { id: "back_squat", name: "Back Squat" },
      prescription: {
        top_set: { sets: 1, reps: 5, target_rpe: 7, load_kg: 120 },
        backoff: [{ sets: 3, reps: 5, load_kg: 107.5 }],
      },
    },
    {
      block_id: "w1d1_acc",
      type: "accessory",
      exercise: { id: "leg_press", name: "Leg Press" },
      prescription: {
        sets: 3,
        reps_range: [10, 15] as [number, number],
        target_rir: 2,
      },
    },
  ],
  metrics: { fatigue_score: 6.5 },
};

describe("SessionCard", () => {
  it("renders day number", () => {
    render(<SessionCard session={session} />);
    expect(screen.getByText("Day 1")).toBeInTheDocument();
  });

  it("renders tags", () => {
    render(<SessionCard session={session} />);
    expect(screen.getByText("lower")).toBeInTheDocument();
    expect(screen.getByText("strength focus")).toBeInTheDocument();
  });

  it("renders all blocks", () => {
    render(<SessionCard session={session} />);
    expect(screen.getByText("Back Squat")).toBeInTheDocument();
    expect(screen.getByText("Leg Press")).toBeInTheDocument();
  });

  it("renders fatigue metrics", () => {
    render(<SessionCard session={session} />);
    const metrics = screen.getByTestId("session-metrics");
    expect(metrics.textContent).toContain("6.5");
  });
});
