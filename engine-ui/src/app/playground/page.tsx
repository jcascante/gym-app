"use client";

import { useState } from "react";

const BASE_URL =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : "http://localhost:8000";

const TABS = [
  { id: "generate", label: "Generate Plan", path: "/api/v1/generate", method: "POST" },
  { id: "alternatives", label: "Alternatives", path: "/api/v1/exercises/alternatives", method: "POST" },
  { id: "apply-overrides", label: "Apply Overrides", path: "/api/v1/plans/apply-overrides", method: "POST" },
  { id: "validate", label: "Validate Definition", path: "/api/v1/validate-definition", method: "POST" },
  { id: "definitions", label: "List Programs", path: "/api/v1/program-definitions", method: "GET" },
  { id: "library", label: "Exercise Library", path: "/api/v1/exercise-library", method: "GET" },
] as const;

type TabId = (typeof TABS)[number]["id"];

const PRESETS: Record<TabId, string> = {
  generate: JSON.stringify(
    {
      program_id: "strength_ul_4w_v1",
      program_version: "1.0.0",
      weeks: 4,
      days_per_week: 4,
      athlete: {
        level: "intermediate",
        time_budget_minutes: 90,
        equipment: ["barbell", "rack", "bench", "dumbbells", "cable", "machine", "pullup_bar"],
        e1rm: { squat: 160, bench: 115, deadlift: 190, ohp: 70 },
      },
      rules: {
        rounding_profile: "plate_2p5kg",
        volume_metric: "hard_sets_weighted",
        hard_set_rule: "RIR_LE_4",
        main_method: "HYBRID",
        accessory_rir_target: 2,
      },
      seed: 42,
    },
    null,
    2
  ),
  alternatives: JSON.stringify(
    {
      exercise_id: "back_squat",
      athlete_equipment: ["barbell", "rack"],
      restrictions: [],
      exclude_ids: [],
      limit: 5,
    },
    null,
    2
  ),
  "apply-overrides": JSON.stringify(
    {
      plan: { _tip: "Paste a GeneratedPlan object from the Generate response here" },
      overrides: [{ block_id: "w1d1_main_lift", new_exercise_id: "front_squat" }],
    },
    null,
    2
  ),
  validate: JSON.stringify(
    {
      program_id: "my_program",
      program_version: "1.0.0",
      name: "My Program",
      description: "Custom training program",
      parameter_spec: { fields: [] },
      template: {
        weeks: { min: 4, max: 12 },
        days_per_week: { min: 3, max: 5 },
        sessions: [],
      },
      prescriptions: {},
      rules: {},
    },
    null,
    2
  ),
  definitions: "",
  library: "",
};

export default function PlaygroundPage() {
  const [activeTab, setActiveTab] = useState<TabId>("generate");
  const [requestBody, setRequestBody] = useState(PRESETS.generate);
  const [response, setResponse] = useState("");
  const [status, setStatus] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [elapsed, setElapsed] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);

  const tab = TABS.find((t) => t.id === activeTab)!;
  const isGet = tab.method === "GET";

  const handleTabChange = (id: TabId) => {
    setActiveTab(id);
    setRequestBody(PRESETS[id]);
    setResponse("");
    setStatus(null);
    setElapsed(null);
  };

  const handleSend = async () => {
    setLoading(true);
    setResponse("");
    setStatus(null);
    const t0 = performance.now();
    try {
      const init: RequestInit = { headers: { "Content-Type": "application/json" } };
      if (!isGet) {
        init.method = "POST";
        init.body = requestBody;
      }
      const res = await fetch(`${BASE_URL}${tab.path}`, init);
      setStatus(res.status);
      const json = await res.json().catch(() => null);
      setResponse(json !== null ? JSON.stringify(json, null, 2) : `HTTP ${res.status}`);
    } catch (err) {
      setResponse(`Network error: ${err instanceof Error ? err.message : String(err)}`);
      setStatus(0);
    } finally {
      setElapsed(Math.round(performance.now() - t0));
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(response).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }).catch(() => {});
  };

  const statusCls =
    status !== null && status >= 200 && status < 300
      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400"
      : "bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400";

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          API Playground
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-slate-400">
          Test engine endpoints with raw JSON. No persistence — every request is
          independent.
        </p>
      </div>

      {/* Tabs */}
      <div className="mb-6 flex gap-1 overflow-x-auto pb-1">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => handleTabChange(t.id)}
            className={`shrink-0 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              activeTab === t.id
                ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-400"
                : "text-gray-500 hover:bg-gray-100 hover:text-gray-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Request panel */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span
                className={`rounded px-2 py-0.5 text-xs font-bold ${
                  isGet
                    ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400"
                    : "bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400"
                }`}
              >
                {tab.method}
              </span>
              <code className="text-xs text-gray-500 dark:text-slate-400">
                {tab.path}
              </code>
            </div>
            {!isGet && (
              <button
                onClick={() => setRequestBody(PRESETS[activeTab])}
                className="text-xs text-gray-400 hover:text-gray-600 dark:text-slate-500 dark:hover:text-slate-300"
              >
                Reset preset
              </button>
            )}
          </div>

          {isGet ? (
            <div className="flex h-48 items-center justify-center rounded-xl border-2 border-dashed border-gray-200 text-sm text-gray-400 dark:border-slate-700 dark:text-slate-500">
              No request body required
            </div>
          ) : (
            <textarea
              value={requestBody}
              onChange={(e) => setRequestBody(e.target.value)}
              spellCheck={false}
              className="h-96 w-full resize-y rounded-xl border border-gray-300 bg-white p-3 font-mono text-xs text-gray-800 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
            />
          )}

          <button
            onClick={handleSend}
            disabled={loading}
            className="flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:bg-indigo-500 disabled:opacity-50 dark:bg-indigo-500 dark:shadow-indigo-500/20 dark:hover:bg-indigo-400"
          >
            {loading && <Spinner />}
            {loading ? "Sending…" : "Send Request"}
          </button>
        </div>

        {/* Response panel */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700 dark:text-slate-300">
                Response
              </span>
              {status !== null && (
                <span className={`rounded px-2 py-0.5 text-xs font-bold ${statusCls}`}>
                  {status === 0 ? "ERR" : status}
                </span>
              )}
              {elapsed !== null && (
                <span className="text-xs text-gray-400 dark:text-slate-500">
                  {elapsed} ms
                </span>
              )}
            </div>
            {response && (
              <button
                onClick={handleCopy}
                className="text-xs text-gray-400 hover:text-gray-600 dark:text-slate-500 dark:hover:text-slate-300"
              >
                {copied ? "Copied!" : "Copy"}
              </button>
            )}
          </div>

          <pre className="h-[27.5rem] overflow-auto rounded-xl border border-gray-200 bg-gray-50 p-3 font-mono text-xs leading-relaxed text-gray-800 dark:border-slate-800 dark:bg-slate-900/50 dark:text-slate-300">
            {response || (
              <span className="text-gray-400 dark:text-slate-600">
                Response will appear here after sending a request
              </span>
            )}
          </pre>
        </div>
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}
