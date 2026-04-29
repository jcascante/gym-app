import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PlanViewer } from "@/components/plan/PlanViewer";
import type { GeneratedPlan } from "@/lib/types";

const plan: GeneratedPlan = {
  program_id: "strength_ul_4w_v1",
  program_version: "1.0.0",
  generated_at: "2026-02-23T12:00:00Z",
  inputs_echo: {},
  weeks: [
    {
      week: 1,
      sessions: [
        {
          day: 1,
          tags: ["lower"],
          blocks: [
            {
              block_id: "w1d1_main",
              type: "main_lift",
              exercise: { id: "back_squat", name: "Back Squat" },
              prescription: {
                top_set: {
                  sets: 1,
                  reps: 5,
                  target_rpe: 7,
                  load_kg: 120,
                },
                backoff: [{ sets: 3, reps: 5, load_kg: 107.5 }],
              },
            },
          ],
          metrics: { fatigue_score: 5.0 },
        },
      ],
    },
  ],
  warnings: [],
  repairs: [],
};

describe("PlanViewer", () => {
  it("renders plan title", () => {
    render(<PlanViewer plan={plan} />);
    expect(
      screen.getByText("strength ul 4w v1")
    ).toBeInTheDocument();
  });

  it("renders week view", () => {
    render(<PlanViewer plan={plan} />);
    expect(screen.getByTestId("week-1")).toBeInTheDocument();
    expect(screen.getByText("Week 1")).toBeInTheDocument();
  });

  it("renders session within week", () => {
    render(<PlanViewer plan={plan} />);
    expect(screen.getByTestId("session-day-1")).toBeInTheDocument();
  });

  it("does not render warnings when empty", () => {
    render(<PlanViewer plan={plan} />);
    expect(screen.queryByTestId("warnings")).not.toBeInTheDocument();
  });

  it("renders warnings when present", () => {
    const planWithWarnings = {
      ...plan,
      warnings: ["Low volume on quads"],
    };
    render(<PlanViewer plan={planWithWarnings} />);
    expect(screen.getByTestId("warnings")).toBeInTheDocument();
    expect(
      screen.getByText("Low volume on quads")
    ).toBeInTheDocument();
  });
});
