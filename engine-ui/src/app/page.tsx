import Link from "next/link";

const features = [
  {
    title: "Strength",
    desc: "Upper/Lower splits with main lifts, top sets + backoffs, and hypertrophy accessories. RPE-periodized across 4 weeks.",
    iconPath: "M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125",
    tagColor: "bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400",
    iconColor: "bg-blue-100 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400",
  },
  {
    title: "Conditioning",
    desc: "Zone 2 steady-state, threshold intervals, and VO2max work. HR-zone or RPE based with progressive overload.",
    iconPath: "M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z",
    tagColor: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400",
    iconColor: "bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400",
  },
  {
    title: "Smart Repair",
    desc: "Automatic constraint validation with fatigue caps, volume limits, and repair strategies to keep plans safe.",
    iconPath: "M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z",
    tagColor: "bg-violet-100 text-violet-700 dark:bg-violet-500/15 dark:text-violet-400",
    iconColor: "bg-violet-100 text-violet-600 dark:bg-violet-500/15 dark:text-violet-400",
  },
];

export default function Home() {
  return (
    <div className="flex flex-col items-center py-12 sm:py-20">
      {/* Status badge */}
      <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-indigo-50 px-4 py-1.5 text-xs font-semibold text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-400">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-500 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-indigo-500" />
        </span>
        Deterministic Engine v1.0
      </div>

      {/* Hero */}
      <h1 className="text-center text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl lg:text-6xl dark:text-white">
        Training Program
        <br />
        <span className="text-indigo-600 dark:text-indigo-400">Generator</span>
      </h1>
      <p className="mt-6 max-w-2xl text-center text-base text-gray-500 sm:text-lg dark:text-slate-400">
        Generate periodized strength and conditioning plans with evidence-based
        programming. RPE-based auto-loading, fatigue management, and
        constraint-aware repair.
      </p>

      {/* CTA buttons */}
      <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:gap-4">
        <Link
          href="/generate"
          className="rounded-xl bg-indigo-600 px-8 py-3 text-center text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:bg-indigo-500 hover:shadow-indigo-500/40 dark:bg-indigo-500 dark:shadow-indigo-500/20 dark:hover:bg-indigo-400"
        >
          Generate a Plan
        </Link>
        <Link
          href="/definitions"
          className="rounded-xl border border-gray-300 bg-white px-8 py-3 text-center text-sm font-semibold text-gray-700 shadow-sm transition-all hover:bg-gray-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
        >
          Browse Programs
        </Link>
      </div>

      {/* Feature cards */}
      <div className="mt-20 grid w-full max-w-5xl gap-6 md:grid-cols-3">
        {features.map((f) => (
          <div
            key={f.title}
            className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-colors dark:border-slate-800 dark:bg-slate-900"
          >
            <div className={`mb-4 flex h-10 w-10 items-center justify-center rounded-lg ${f.iconColor}`}>
              <svg
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d={f.iconPath} />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-gray-900 dark:text-white">
              {f.title}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-gray-500 dark:text-slate-400">
              {f.desc}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
