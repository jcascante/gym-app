"use client";

import type { ExerciseAlternative, GeneratedPlan } from "@/lib/types";
import { WeekView } from "./WeekView";

interface PlanViewerProps {
  plan: GeneratedPlan;
  editable?: boolean;
  athleteEquipment?: string[];
  onSwapComplete?: (blockId: string, newExercise: ExerciseAlternative) => void;
  onImportJson?: () => void;
}

function handleExportJson(plan: GeneratedPlan) {
  const blob = new Blob([JSON.stringify(plan, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${plan.program_id}_plan.json`;
  a.click();
  URL.revokeObjectURL(url);
}

export function PlanViewer({ plan, editable = false, athleteEquipment = [], onSwapComplete, onImportJson }: PlanViewerProps) {
  return (
    <div data-testid="plan-viewer">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">
            {plan.program_id.replace(/_/g, " ")}
          </h1>
          <p className="mt-1 text-sm text-gray-400 dark:text-slate-500">
            v{plan.program_version} &mdash; Generated{" "}
            {new Date(plan.generated_at).toLocaleDateString()}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400">
            {plan.weeks.length} weeks &bull; {plan.weeks[0]?.sessions.length ?? 0} days/wk
          </span>
          {onImportJson && (
            <button
              onClick={onImportJson}
              data-testid="import-json-btn"
              className="rounded-md border border-gray-200 bg-white px-3 py-1 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              Load JSON
            </button>
          )}
          <button
            onClick={() => handleExportJson(plan)}
            data-testid="export-json-btn"
            className="rounded-md border border-gray-200 bg-white px-3 py-1 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
          >
            Export JSON
          </button>
        </div>
      </div>

      <div className="space-y-10">
        {plan.weeks.map((week) => (
          <WeekView
            key={week.week}
            week={week}
            editable={editable}
            athleteEquipment={athleteEquipment}
            onSwapComplete={onSwapComplete}
          />
        ))}
      </div>

      {plan.warnings.length > 0 && (
        <div
          className="mt-8 rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-500/30 dark:bg-amber-500/10"
          data-testid="warnings"
        >
          <h3 className="font-semibold text-amber-800 dark:text-amber-400">Warnings</h3>
          <ul className="mt-2 list-disc pl-4 text-sm text-amber-700 dark:text-amber-300">
            {plan.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
