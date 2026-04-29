"use client";

import { useState } from "react";
import { StepHeader } from "../shared/StepHeader";
import { buildDefinition, validateDefinitionStructure } from "@/lib/wizard/buildDefinition";
import { validateDefinition, ApiError } from "@/lib/api-client";
import type { WizardState } from "@/lib/wizard/types";

interface Props {
  state: WizardState;
}

export function Step5Review({ state }: Props) {
  const [jsonOpen, setJsonOpen] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    errors: string[];
    source: "frontend" | "backend" | "unavailable";
  } | null>(null);

  const definition = buildDefinition(state);
  const { step1, step2, step3 } = state;
  const totalBlocks = step3.sessions.reduce((sum, s) => sum + s.blocks.length, 0);

  const handleValidate = async () => {
    setValidating(true);
    setValidationResult(null);

    // Frontend structural check first
    const structureErrors = validateDefinitionStructure(definition);
    if (structureErrors.length > 0) {
      setValidationResult({ valid: false, errors: structureErrors, source: "frontend" });
      setValidating(false);
      return;
    }

    // Try backend validation
    try {
      const result = await validateDefinition(definition);
      setValidationResult({ ...result, source: "backend" });
    } catch (err) {
      if (err instanceof ApiError && (err.status === 404 || err.status === 405)) {
        setValidationResult({
          valid: true,
          errors: ["Validation service unavailable — download and test with the generate endpoint."],
          source: "unavailable",
        });
      } else {
        setValidationResult({
          valid: false,
          errors: [err instanceof Error ? err.message : "Validation failed"],
          source: "backend",
        });
      }
    } finally {
      setValidating(false);
    }
  };

  const handleDownload = () => {
    const json = JSON.stringify(definition, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${String(definition.program_id)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <StepHeader
        title="Review & Download"
        subtitle="Check your program summary, validate the structure, then download the JSON file."
      />

      {/* Summary card */}
      <div className="rounded-xl border border-gray-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
        <h3 className="mb-4 text-sm font-bold text-gray-900 dark:text-white">Program Summary</h3>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">Name</dt>
            <dd className="mt-0.5 font-medium text-gray-900 dark:text-white">{step1.name || "—"}</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">Type</dt>
            <dd className="mt-0.5 capitalize font-medium text-gray-900 dark:text-white">{step1.programType}</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">Duration</dt>
            <dd className="mt-0.5 font-medium text-gray-900 dark:text-white">{step1.durationWeeks} weeks</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">Frequency</dt>
            <dd className="mt-0.5 font-medium text-gray-900 dark:text-white">{step1.frequencyDays} days/week</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">Sessions</dt>
            <dd className="mt-0.5 font-medium text-gray-900 dark:text-white">{step2.activeDays.length}</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">Total Blocks</dt>
            <dd className="mt-0.5 font-medium text-gray-900 dark:text-white">{totalBlocks}</dd>
          </div>
          <div className="col-span-2">
            <dt className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">Program ID</dt>
            <dd className="mt-0.5 font-mono text-xs text-gray-600 dark:text-slate-400">{String(definition.program_id)}</dd>
          </div>
        </dl>
      </div>

      {/* JSON preview */}
      <div className="rounded-xl border border-gray-200 dark:border-slate-700">
        <button
          type="button"
          onClick={() => setJsonOpen((o) => !o)}
          className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-slate-300"
        >
          <span>JSON Preview</span>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className={`transition-transform ${jsonOpen ? "rotate-180" : ""}`}
          >
            <path d="M6 9l6 6 6-6" />
          </svg>
        </button>
        {jsonOpen && (
          <pre className="max-h-80 overflow-auto rounded-b-xl bg-gray-50 p-4 text-xs text-gray-700 dark:bg-slate-800 dark:text-slate-300">
            {JSON.stringify(definition, null, 2)}
          </pre>
        )}
      </div>

      {/* Validation result */}
      {validationResult && (
        <div
          className={`rounded-lg p-4 text-sm ${
            validationResult.source === "unavailable"
              ? "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400"
              : validationResult.valid
              ? "bg-green-50 text-green-700 dark:bg-green-500/10 dark:text-green-400"
              : "bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-400"
          }`}
        >
          {validationResult.source !== "unavailable" && (
            <p className="font-semibold">
              {validationResult.valid ? "Valid definition" : "Validation failed"}
            </p>
          )}
          {validationResult.errors.map((e, i) => (
            <p key={i} className="mt-1 text-xs">
              {e}
            </p>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <button
          type="button"
          onClick={handleValidate}
          disabled={validating}
          className="flex items-center gap-2 rounded-xl border border-gray-300 px-5 py-3 text-sm font-semibold text-gray-700 transition-all hover:bg-gray-50 disabled:opacity-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          {validating && (
            <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}
          Validate
        </button>

        <button
          type="button"
          onClick={handleDownload}
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:bg-indigo-500 dark:bg-indigo-500 dark:shadow-indigo-500/20 dark:hover:bg-indigo-400"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" />
          </svg>
          Download JSON
        </button>
      </div>
    </div>
  );
}
