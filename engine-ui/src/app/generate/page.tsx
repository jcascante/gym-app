"use client";

import { useState, useEffect, useRef } from "react";
import type { ChangeEvent, ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  generatePlan,
  listProgramDefinitions,
  getProgramDefinition,
  applyOverrides,
  ApiError,
} from "@/lib/api-client";
import type {
  ExerciseAlternative,
  GeneratedPlan,
  ProgramDefinitionFull,
  ParameterField,
} from "@/lib/types";
import { PlanViewer } from "@/components/plan/PlanViewer";

const ALL_EQUIPMENT = [
  "barbell", "rack", "bench", "dumbbell", "cable_machine", "kettlebell",
  "pull_up_bar", "smith_machine", "dip_station", "back_raise_bench",
  "assisted_dip_machine", "machine", "bands",
];

function parseDefaultExpr(
  expr: string | undefined,
  type: string,
  enumValues?: string[]
): unknown {
  if (!expr) {
    if (type === "string_array") return [];
    if (type === "number") return 0;
    if (type === "boolean") return false;
    if (type === "enum") return enumValues?.[0] ?? "";
    return "";
  }
  if (expr === "[]") return [];
  if (expr === "true") return true;
  if (expr === "false") return false;
  const num = Number(expr);
  if (!isNaN(num) && expr.trim() !== "") return num;
  const strMatch = expr.match(/^'(.+)'$/);
  if (strMatch) return strMatch[1];
  return "";
}

function evaluateCondition(
  expr: string | undefined,
  values: Record<string, unknown>
): boolean {
  if (!expr) return true;
  return expr.split("&&").every((part) => {
    const m = part.trim().match(/ctx\.([a-z_.]+)\s*==\s*'?([^'\s)]+)'?/);
    if (m) return String(values[m[1]] ?? "") === m[2];
    return true;
  });
}

function buildNestedObject(
  flat: Record<string, unknown>
): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, val] of Object.entries(flat)) {
    const parts = key.split(".");
    let cur: Record<string, unknown> = result;
    for (let i = 0; i < parts.length - 1; i++) {
      if (typeof cur[parts[i]] !== "object" || cur[parts[i]] === null) {
        cur[parts[i]] = {};
      }
      cur = cur[parts[i]] as Record<string, unknown>;
    }
    cur[parts[parts.length - 1]] = val;
  }
  return result;
}

export default function GeneratePage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [fieldValues, setFieldValues] = useState<Record<string, unknown>>({});
  const [weeks, setWeeks] = useState(4);
  const [daysPerWeek, setDaysPerWeek] = useState(4);
  const [plan, setPlan] = useState<GeneratedPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [swapError, setSwapError] = useState<string | null>(null);
  const importRef = useRef<HTMLInputElement>(null);

  const athleteEquipment =
    (fieldValues["athlete.equipment"] as string[] | undefined) ?? [];

  const { data: definitions, isLoading: defsLoading } = useQuery({
    queryKey: ["definitions"],
    queryFn: listProgramDefinitions,
  });

  const { data: selectedDef } = useQuery({
    queryKey: ["definition", selectedId],
    queryFn: () => getProgramDefinition(selectedId!),
    enabled: !!selectedId,
  });

  useEffect(() => {
    if (!selectedDef) return;
    const initial: Record<string, unknown> = {};
    for (const field of selectedDef.parameter_spec.fields) {
      initial[field.key] = parseDefaultExpr(field.default_expr, field.type, field.enum);
    }
    setFieldValues(initial);
    setWeeks(selectedDef.template.weeks.min);
    setDaysPerWeek(selectedDef.template.days_per_week.min);
    setPlan(null);
    setError(null);
  }, [selectedDef]);

  const updateField = (key: string, value: unknown) => {
    setFieldValues((prev: Record<string, unknown>) => ({ ...prev, [key]: value }));
  };

  const handleSwapComplete = async (blockId: string, newExercise: ExerciseAlternative) => {
    if (!plan) return;
    setSwapError(null);
    try {
      const result = await applyOverrides({
        plan,
        overrides: [{ block_id: blockId, new_exercise_id: newExercise.id }],
      });
      if (result.rejected.length > 0) {
        setSwapError(`Swap rejected: ${result.rejected[0].reason.replace(/_/g, " ")}`);
      } else {
        setPlan(result.plan);
      }
    } catch {
      setSwapError("Failed to apply swap — is the backend running?");
    }
  };

  const handleImportJson = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const json = JSON.parse(evt.target?.result as string);
        setPlan(json as GeneratedPlan);
        setError(null);
        setSwapError(null);
      } catch {
        setError("Invalid JSON file — could not parse plan.");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  const handleGenerate = async () => {
    if (!selectedId || !selectedDef) return;
    setLoading(true);
    setError(null);
    setPlan(null);
    try {
      // Only include fields that are visible (required_if/visible_if satisfied)
      const visibleValues: Record<string, unknown> = {};
      for (const field of selectedDef.parameter_spec.fields) {
        const condExpr = field.visible_if ?? field.required_if;
        if (evaluateCondition(condExpr, fieldValues)) {
          visibleValues[field.key] = fieldValues[field.key];
        }
      }
      const nested = buildNestedObject(visibleValues);
      const request = {
        program_id: selectedId,
        program_version: selectedDef.version,
        weeks,
        days_per_week: daysPerWeek,
        ...nested,
      };
      const result = await generatePlan(request as never);
      setPlan(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`API Error (${err.status}): ${err.message}`);
      } else {
        setError("An unexpected error occurred");
      }
    } finally {
      setLoading(false);
    }
  };

  const inputCls =
    "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none transition-colors focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:focus:border-indigo-400 dark:focus:ring-indigo-400/20";

  const renderField = (field: ParameterField) => {
    const condExpr = field.visible_if ?? field.required_if;
    if (!evaluateCondition(condExpr, fieldValues)) return null;

    const rawLabel = field.description ?? field.key.split(".").pop()?.replace(/_/g, " ");
    const label = rawLabel ?? field.key;
    const value = fieldValues[field.key];

    if (field.type === "string_array" && field.key.includes("equipment")) {
      const arr = (value as string[]) ?? [];
      return (
        <div key={field.key} className="col-span-2">
          <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
            Equipment
          </label>
          <div className="flex flex-wrap gap-2">
            {ALL_EQUIPMENT.map((item) => {
              const sel = arr.includes(item);
              return (
                <button
                  key={item}
                  type="button"
                  onClick={() =>
                    updateField(
                      field.key,
                      sel ? arr.filter((e) => e !== item) : [...arr, item]
                    )
                  }
                  className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-all ${
                    sel
                      ? "border-indigo-600 bg-indigo-600 text-white dark:border-indigo-500 dark:bg-indigo-500"
                      : "border-gray-300 text-gray-500 hover:border-gray-400 dark:border-slate-600 dark:text-slate-400"
                  }`}
                >
                  {item.replace(/_/g, " ")}
                </button>
              );
            })}
          </div>
        </div>
      );
    }

    if (field.type === "enum" && field.enum) {
      return (
        <div key={field.key}>
          <Field label={label}>
            <select
              value={String(value ?? "")}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => updateField(field.key, e.target.value)}
              className={inputCls}
            >
              {field.enum.map((opt) => (
                <option key={opt} value={opt}>
                  {opt.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </Field>
        </div>
      );
    }

    if (field.type === "number") {
      return (
        <div key={field.key}>
          <Field label={label}>
            <input
              type="number"
              value={Number(value ?? 0)}
              onChange={(e: ChangeEvent<HTMLInputElement>) => updateField(field.key, +e.target.value)}
              min={field.min}
              max={field.max}
              className={inputCls}
            />
          </Field>
        </div>
      );
    }

    if (field.type === "boolean") {
      return (
        <div key={field.key} className="flex items-center gap-3 py-1">
          <input
            type="checkbox"
            id={field.key}
            checked={Boolean(value)}
            onChange={(e) => updateField(field.key, e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-indigo-600"
          />
          <label
            htmlFor={field.key}
            className="text-xs font-medium text-gray-600 dark:text-slate-400"
          >
            {label}
          </label>
        </div>
      );
    }

    if (field.type === "string_array") {
      return (
        <div key={field.key}>
          <Field label={label}>
            <input
              type="text"
              value={((value as string[]) ?? []).join(", ")}
              onChange={(e: ChangeEvent<HTMLInputElement>) =>
                updateField(
                  field.key,
                  e.target.value
                    .split(",")
                    .map((s: string) => s.trim())
                    .filter(Boolean)
                )
              }
              placeholder="comma-separated values"
              className={inputCls}
            />
          </Field>
        </div>
      );
    }

    return (
      <div key={field.key}>
        <Field label={label}>
          <input
            type="text"
            value={String(value ?? "")}
            onChange={(e: ChangeEvent<HTMLInputElement>) => updateField(field.key, e.target.value)}
            className={inputCls}
          />
        </Field>
      </div>
    );
  };

  const groupedFields = (): Record<string, ParameterField[]> => {
    if (!selectedDef) return {};
    const groups: Record<string, ParameterField[]> = {};
    for (const field of selectedDef.parameter_spec.fields) {
      const group = field.key.split(".")[0];
      if (!groups[group]) groups[group] = [];
      groups[group].push(field);
    }
    return groups;
  };

  const groups = groupedFields();
  const weeksFixed =
    selectedDef &&
    selectedDef.template.weeks.min === selectedDef.template.weeks.max;
  const daysFixed =
    selectedDef &&
    selectedDef.template.days_per_week.min ===
      selectedDef.template.days_per_week.max;

  return (
    <div>
      {/* Hidden import input — always mounted so ref works from any button */}
      <input
        ref={importRef}
        type="file"
        accept=".json"
        onChange={handleImportJson}
        className="sr-only"
      />

      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Generate Training Plan
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-slate-400">
            Select a program definition and configure your athlete profile.
          </p>
        </div>
        <button
          onClick={() => importRef.current?.click()}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-500 hover:border-gray-400 hover:text-gray-700 dark:border-slate-600 dark:text-slate-400 dark:hover:border-slate-500 dark:hover:text-slate-200"
        >
          Load from JSON
        </button>
      </div>

      {/* Definition selector */}
      <div className="mb-6">
        <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
          Program
        </label>
        {defsLoading ? (
          <div className="text-sm text-gray-400">Loading programs...</div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {(definitions ?? []).map((def) => (
              <button
                key={def.program_id}
                type="button"
                onClick={() => setSelectedId(def.program_id)}
                className={`rounded-xl border p-4 text-left transition-all ${
                  selectedId === def.program_id
                    ? "border-indigo-600 bg-indigo-50 ring-2 ring-indigo-500/30 dark:border-indigo-500 dark:bg-indigo-500/10"
                    : "border-gray-200 bg-white hover:border-gray-300 dark:border-slate-700 dark:bg-slate-900 dark:hover:border-slate-600"
                }`}
              >
                <div className="text-sm font-semibold text-gray-900 dark:text-white">
                  {def.name ?? def.program_id}
                </div>
                {def.description && (
                  <div className="mt-1 line-clamp-2 text-xs text-gray-500 dark:text-slate-400">
                    {def.description}
                  </div>
                )}
                <div className="mt-2 text-xs text-gray-400 dark:text-slate-500">
                  v{def.version}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedId && selectedDef && (
        <div className="grid gap-8 lg:grid-cols-[380px_1fr]">
          {/* Sidebar form */}
          <div className="space-y-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            {/* Schedule */}
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
                Schedule
              </label>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Weeks">
                  <input
                    type="number"
                    value={weeks}
                    onChange={(e) => setWeeks(+e.target.value)}
                    min={selectedDef.template.weeks.min}
                    max={selectedDef.template.weeks.max}
                    disabled={weeksFixed ?? false}
                    className={inputCls}
                  />
                </Field>
                <Field label="Days / Week">
                  <input
                    type="number"
                    value={daysPerWeek}
                    onChange={(e) => setDaysPerWeek(+e.target.value)}
                    min={selectedDef.template.days_per_week.min}
                    max={selectedDef.template.days_per_week.max}
                    disabled={daysFixed ?? false}
                    className={inputCls}
                  />
                </Field>
              </div>
            </div>

            {/* Dynamic parameter groups */}
            {Object.entries(groups).map(([group, fields]) => (
              <div key={group}>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
                  {group.replace(/_/g, " ")}
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {fields.map(renderField)}
                </div>
              </div>
            ))}

            {/* Generate */}
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:bg-indigo-500 disabled:opacity-50 dark:bg-indigo-500 dark:shadow-indigo-500/20 dark:hover:bg-indigo-400"
            >
              {loading && <Spinner />}
              {loading ? "Generating..." : "Generate Plan"}
            </button>

            {error && (
              <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-500/10 dark:text-red-400">
                {error}
              </div>
            )}
          </div>

          {/* Result */}
          <div className="min-w-0">
            {swapError && (
              <div className="mb-4 flex items-center justify-between rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-500/10 dark:text-red-400">
                {swapError}
                <button
                  onClick={() => setSwapError(null)}
                  className="ml-4 text-red-400 hover:text-red-600"
                  aria-label="Dismiss"
                >
                  ✕
                </button>
              </div>
            )}
            {plan ? (
              <PlanViewer
                plan={plan}
                editable
                athleteEquipment={athleteEquipment}
                onSwapComplete={handleSwapComplete}
                onImportJson={() => importRef.current?.click()}
              />
            ) : (
              <div className="flex h-80 flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 dark:border-slate-700">
                {loading ? (
                  <div className="flex flex-col items-center gap-3">
                    <Spinner className="h-8 w-8 text-indigo-500" />
                    <span className="text-sm text-gray-400 dark:text-slate-500">
                      Generating your plan...
                    </span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-3 text-gray-400 dark:text-slate-500">
                    <svg
                      className="h-10 w-10"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    <span className="text-sm">Configure and generate a plan</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {!selectedId && !defsLoading && !plan && (
        <div className="flex h-48 items-center justify-center rounded-xl border-2 border-dashed border-gray-300 dark:border-slate-700">
          <div className="flex flex-col items-center gap-3 text-gray-400 dark:text-slate-500">
            <span className="text-sm">Select a program above to configure and generate a plan</span>
            <span className="text-xs">or</span>
            <button
              onClick={() => importRef.current?.click()}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-500 hover:border-gray-400 hover:text-gray-700 dark:border-slate-600 dark:text-slate-400 dark:hover:border-slate-500"
            >
              Load plan from JSON
            </button>
          </div>
        </div>
      )}

      {!selectedId && !defsLoading && plan && (
        <div className="mt-4">
          {swapError && (
            <div className="mb-4 flex items-center justify-between rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-500/10 dark:text-red-400">
              {swapError}
              <button onClick={() => setSwapError(null)} className="ml-4 text-red-400 hover:text-red-600" aria-label="Dismiss">✕</button>
            </div>
          )}
          <PlanViewer
            plan={plan}
            editable
            athleteEquipment={[]}
            onSwapComplete={handleSwapComplete}
            onImportJson={() => importRef.current?.click()}
          />
        </div>
      )}
    </div>
  );
}

function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none">
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium capitalize text-gray-600 dark:text-slate-400">
        {label}
      </label>
      {children}
    </div>
  );
}
