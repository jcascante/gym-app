"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getExerciseLibrary } from "@/lib/api-client";
import type { ExerciseLibraryEntry } from "@/lib/types";

const PATTERN_COLORS: Record<string, string> = {
  squat: "bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400",
  hip_hinge: "bg-indigo-100 text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-400",
  horizontal_push: "bg-violet-100 text-violet-700 dark:bg-violet-500/15 dark:text-violet-400",
  horizontal_pull: "bg-purple-100 text-purple-700 dark:bg-purple-500/15 dark:text-purple-400",
  vertical_push: "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400",
  vertical_pull: "bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-400",
  core: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400",
  conditioning: "bg-cyan-100 text-cyan-700 dark:bg-cyan-500/15 dark:text-cyan-400",
};

function patternCls(pattern: string): string {
  return (
    PATTERN_COLORS[pattern] ??
    "bg-gray-100 text-gray-600 dark:bg-slate-700 dark:text-slate-300"
  );
}

export default function LibraryPage() {
  const [search, setSearch] = useState("");
  const [selectedPattern, setSelectedPattern] = useState<string | null>(null);
  const [selectedSwapGroup, setSelectedSwapGroup] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["exercise-library"],
    queryFn: getExerciseLibrary,
    staleTime: 5 * 60 * 1000,
  });

  const exercises = data?.exercises ?? [];

  const allPatterns = [...new Set(exercises.flatMap((e) => e.patterns))].sort();
  const allSwapGroups = [
    ...new Set(
      exercises.map((e) => e.swap_group).filter((g): g is string => g !== null)
    ),
  ].sort();

  const filtered = exercises.filter((e) => {
    if (
      search &&
      !e.name.toLowerCase().includes(search.toLowerCase()) &&
      !e.id.toLowerCase().includes(search.toLowerCase())
    )
      return false;
    if (selectedPattern && !e.patterns.includes(selectedPattern)) return false;
    if (selectedSwapGroup && e.swap_group !== selectedSwapGroup) return false;
    return true;
  });

  const filterBtnCls = (active: boolean) =>
    `rounded-full border px-3 py-1 text-xs font-medium transition-all ${
      active
        ? "border-indigo-600 bg-indigo-600 text-white dark:border-indigo-500 dark:bg-indigo-500"
        : "border-gray-300 text-gray-500 hover:border-gray-400 dark:border-slate-600 dark:text-slate-400 dark:hover:border-slate-500"
    }`;

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Exercise Library
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-slate-400">
          {isLoading
            ? "Loading..."
            : `${exercises.length} exercises`}
          {data?.version ? ` — v${data.version}` : ""}
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6 space-y-4">
        <input
          type="search"
          placeholder="Search by name or ID…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full max-w-sm rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        />

        {allPatterns.length > 0 && (
          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
              Movement Pattern
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSelectedPattern(null)}
                className={filterBtnCls(!selectedPattern)}
              >
                All
              </button>
              {allPatterns.map((p) => (
                <button
                  key={p}
                  onClick={() =>
                    setSelectedPattern(selectedPattern === p ? null : p)
                  }
                  className={filterBtnCls(selectedPattern === p)}
                >
                  {p.replace(/_/g, " ")}
                </button>
              ))}
            </div>
          </div>
        )}

        {allSwapGroups.length > 0 && (
          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
              Swap Group
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSelectedSwapGroup(null)}
                className={filterBtnCls(!selectedSwapGroup)}
              >
                All
              </button>
              {allSwapGroups.map((g) => (
                <button
                  key={g}
                  onClick={() =>
                    setSelectedSwapGroup(selectedSwapGroup === g ? null : g)
                  }
                  className={filterBtnCls(selectedSwapGroup === g)}
                >
                  {g.replace(/_/g, " ")}
                </button>
              ))}
            </div>
          </div>
        )}

        {!isLoading && (
          <p className="text-xs text-gray-400 dark:text-slate-500">
            Showing {filtered.length} of {exercises.length} exercises
          </p>
        )}
      </div>

      {isError && (
        <div className="mb-6 rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-500/10 dark:text-red-400">
          Failed to load exercise library. Make sure the backend is running.
        </div>
      )}

      {isLoading ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 9 }).map((_, i) => (
            <div
              key={i}
              className="h-36 animate-pulse rounded-xl bg-gray-100 dark:bg-slate-800"
            />
          ))}
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((ex) => (
            <ExerciseCard key={ex.id} exercise={ex} />
          ))}
          {filtered.length === 0 && (
            <div className="col-span-3 flex h-32 items-center justify-center text-sm text-gray-400 dark:text-slate-500">
              No exercises match your filters
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ExerciseCard({ exercise: ex }: { exercise: ExerciseLibraryEntry }) {
  const fatigueWidth = Math.min((ex.fatigue_cost / 2.5) * 100, 100);
  const fatigueColor =
    ex.fatigue_cost > 1.8
      ? "bg-red-400"
      : ex.fatigue_cost > 1.2
        ? "bg-amber-400"
        : "bg-emerald-400";

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate font-semibold text-gray-900 dark:text-white">
            {ex.name}
          </div>
          <div className="font-mono text-xs text-gray-400 dark:text-slate-500">
            {ex.id}
          </div>
        </div>
        {ex.swap_group && (
          <span className="shrink-0 rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600 dark:bg-slate-700 dark:text-slate-300">
            {ex.swap_group.replace(/_/g, " ")}
          </span>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-1">
        {ex.patterns.map((p) => (
          <span
            key={p}
            className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${patternCls(p)}`}
          >
            {p.replace(/_/g, " ")}
          </span>
        ))}
      </div>

      {ex.equipment.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {ex.equipment.map((eq) => (
            <span
              key={eq}
              className="rounded bg-gray-50 px-1.5 py-0.5 text-[10px] text-gray-500 ring-1 ring-gray-200 dark:bg-slate-800 dark:text-slate-400 dark:ring-slate-700"
            >
              {eq.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      )}

      <div className="mt-3">
        <div className="mb-1 flex items-center justify-between text-xs">
          <span className="text-gray-400 dark:text-slate-500">Fatigue cost</span>
          <span className="font-mono text-gray-600 dark:text-slate-300">
            {ex.fatigue_cost.toFixed(1)}
          </span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-slate-800">
          <div
            className={`h-full rounded-full ${fatigueColor}`}
            style={{ width: `${fatigueWidth}%` }}
          />
        </div>
      </div>
    </div>
  );
}
