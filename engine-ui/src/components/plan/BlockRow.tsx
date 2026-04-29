"use client";

import type { ExerciseAlternative, PlanBlock } from "@/lib/types";
import {
  isConditioningPrescription,
  isIntervalPrescription,
  isRepsRangePrescription,
  isStrengthPrescription,
} from "@/lib/types";
import { getExerciseAlternatives } from "@/lib/api-client";
import { formatDuration, formatLoad } from "@/lib/utils";
import { useState } from "react";

function typeBadgeCls(type: string): string {
  if (type.includes("main_lift") || type.includes("conditional_block"))
    return "bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400";
  if (type.includes("accessory"))
    return "bg-violet-100 text-violet-700 dark:bg-violet-500/15 dark:text-violet-400";
  if (type.includes("steady"))
    return "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400";
  if (type.includes("intervals"))
    return "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400";
  return "bg-gray-100 text-gray-600 dark:bg-slate-700 dark:text-slate-300";
}

interface BlockRowProps {
  block: PlanBlock;
  editable?: boolean;
  athleteEquipment?: string[];
  onSwapComplete?: (blockId: string, newExercise: ExerciseAlternative) => void;
}

export function BlockRow({
  block,
  editable = false,
  athleteEquipment = [],
  onSwapComplete,
}: BlockRowProps) {
  const rx = block.prescription;
  const [showAlternatives, setShowAlternatives] = useState(false);
  const [alternatives, setAlternatives] = useState<ExerciseAlternative[]>([]);
  const [loadingAlts, setLoadingAlts] = useState(false);
  const [altError, setAltError] = useState<string | null>(null);

  async function handleSwapClick() {
    if (showAlternatives) {
      setShowAlternatives(false);
      return;
    }
    setLoadingAlts(true);
    setAltError(null);
    try {
      const result = await getExerciseAlternatives({
        exercise_id: block.exercise.id,
        athlete_equipment: athleteEquipment,
      });
      setAlternatives(result.alternatives);
      setShowAlternatives(true);
    } catch {
      setAltError("Failed to load alternatives");
    } finally {
      setLoadingAlts(false);
    }
  }

  function handleSelectAlternative(alt: ExerciseAlternative) {
    setShowAlternatives(false);
    onSwapComplete?.(block.block_id, alt);
  }

  return (
    <div
      className="border-b border-gray-100 py-3 last:border-b-0 dark:border-slate-800"
      data-testid={`block-${block.block_id}`}
    >
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-gray-900 dark:text-slate-100">
          {block.exercise.name}
        </span>
        <span className={`rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${typeBadgeCls(block.type)}`}>
          {block.type.replace(/_/g, " ")}
        </span>
        {editable && (
          <button
            onClick={handleSwapClick}
            disabled={loadingAlts}
            aria-label="Swap exercise"
            data-testid={`swap-btn-${block.block_id}`}
            className="ml-auto rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 disabled:opacity-50 dark:hover:bg-slate-700 dark:hover:text-slate-300"
          >
            {loadingAlts ? (
              <span className="text-xs">…</span>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                <path d="M8 5a1 1 0 0 0 0 2h4.586l-1.293 1.293a1 1 0 0 0 1.414 1.414l3-3a1 1 0 0 0 0-1.414l-3-3A1 1 0 0 0 12.586 3H8a1 1 0 0 0 0 2zM12 15a1 1 0 0 0 0-2H7.414l1.293-1.293a1 1 0 0 0-1.414-1.414l-3 3a1 1 0 0 0 0 1.414l3 3A1 1 0 0 0 9.414 17H12a1 1 0 0 0 0-2z" />
              </svg>
            )}
          </button>
        )}
      </div>
      <div className="mt-1.5 text-sm text-gray-500 dark:text-slate-400">
        {isStrengthPrescription(rx) && (
          <span data-testid="strength-rx" className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span className="flex items-center gap-1">
              <span className="font-mono text-xs text-indigo-600 dark:text-indigo-400">Top set</span>
              {rx.top_set.sets} sets &times; {rx.top_set.reps} reps @ {formatLoad(rx.top_set.load_kg)}
              <span className="opacity-60">RPE {rx.top_set.target_rpe}</span>
            </span>
            {rx.backoff.length > 0 && (
              <span className="flex items-center gap-1">
                <span className="font-mono text-xs text-gray-400 dark:text-slate-500">Backoff</span>
                {rx.backoff[0].sets} sets &times; {rx.backoff[0].reps} reps @ {formatLoad(rx.backoff[0].load_kg)}
              </span>
            )}
          </span>
        )}
        {isRepsRangePrescription(rx) && (
          <span data-testid="reps-range-rx">
            {rx.sets} sets &times; {rx.reps_range[0]}-{rx.reps_range[1]} reps
            <span className="opacity-60"> @ RIR {rx.target_rir}</span>
          </span>
        )}
        {isConditioningPrescription(rx) && (
          <span data-testid="conditioning-rx">
            {formatDuration(rx.duration_minutes)}
            <span className="opacity-60"> &mdash; {rx.intensity.target}</span>
          </span>
        )}
        {isIntervalPrescription(rx) && (
          <span data-testid="interval-rx">
            {rx.work.intervals}&times;
            {rx.work.minutes_each ? `${rx.work.minutes_each}min` : `${rx.work.seconds_each}s`}
            <span className="opacity-60"> &mdash; {rx.work.intensity.target}</span>
          </span>
        )}
      </div>
      {altError && (
        <p className="mt-1 text-xs text-red-500" data-testid="alt-error">{altError}</p>
      )}
      {showAlternatives && (
        <ul
          className="mt-2 space-y-1 rounded-md border border-gray-100 bg-gray-50 p-2 dark:border-slate-700 dark:bg-slate-800"
          data-testid="alternatives-list"
        >
          {alternatives.length === 0 ? (
            <li className="text-xs text-gray-400 dark:text-slate-500">No alternatives available</li>
          ) : (
            alternatives.map((alt) => (
              <li key={alt.id}>
                <button
                  onClick={() => handleSelectAlternative(alt)}
                  data-testid={`alt-${alt.id}`}
                  className="w-full rounded px-2 py-1 text-left text-sm hover:bg-gray-100 dark:hover:bg-slate-700"
                >
                  <span className="font-medium text-gray-800 dark:text-slate-100">{alt.name}</span>
                  <span className="ml-2 text-xs text-gray-400 dark:text-slate-500">
                    {alt.match_reason === "swap_group" ? "same group" : "similar pattern"}
                  </span>
                </button>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
