"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { listProgramDefinitions } from "@/lib/api-client";

export default function DefinitionsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["definitions"],
    queryFn: listProgramDefinitions,
  });

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Available Programs
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-slate-400">
          Browse program templates that the engine can generate plans from.
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center gap-3 py-12">
          <svg className="h-5 w-5 animate-spin text-indigo-500" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span className="text-sm text-gray-400 dark:text-slate-500">Loading programs...</span>
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-500/10 dark:text-red-400">
          Failed to load programs. Make sure the backend is running on port 8000.
        </div>
      )}

      {data && (
        <div className="grid gap-4 md:grid-cols-2">
          {data.map((def) => (
            <div
              key={def.program_id}
              className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-all hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {def.name ?? def.program_id}
                  </h3>
                  <p className="mt-0.5 text-xs text-gray-400 dark:text-slate-500">
                    {def.program_id}
                  </p>
                </div>
                <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400">
                  v{def.version}
                </span>
              </div>
              {def.description && (
                <p className="mt-3 text-sm leading-relaxed text-gray-500 dark:text-slate-400">
                  {def.description}
                </p>
              )}
              <div className="mt-4">
                <Link
                  href="/generate"
                  className="text-sm font-medium text-indigo-600 underline-offset-2 hover:underline dark:text-indigo-400"
                >
                  Generate with this program &rarr;
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
