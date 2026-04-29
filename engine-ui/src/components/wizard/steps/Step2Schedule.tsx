import { StepHeader } from "../shared/StepHeader";
import type { Step2Data, FrequencyDays, ScheduledDay, SessionType } from "@/lib/wizard/types";

interface Props {
  data: Step2Data;
  frequencyDays: FrequencyDays;
  onChange: (data: Step2Data) => void;
}

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const SESSION_TYPE_OPTIONS: { value: SessionType; label: string }[] = [
  { value: "upper_body", label: "Upper Body" },
  { value: "lower_body", label: "Lower Body" },
  { value: "push", label: "Push" },
  { value: "pull", label: "Pull" },
  { value: "full_body", label: "Full Body" },
  { value: "conditioning", label: "Conditioning" },
];

const selectCls =
  "rounded-lg border border-gray-300 bg-white px-2 py-1 text-xs text-gray-900 outline-none transition-colors focus:border-indigo-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100";

export function Step2Schedule({ data, frequencyDays, onChange }: Props) {
  const activeCount = data.activeDays.length;

  const toggleDay = (dayIndex: number) => {
    const existing = data.activeDays.find((d) => d.dayIndex === dayIndex);
    if (existing) {
      onChange({ activeDays: data.activeDays.filter((d) => d.dayIndex !== dayIndex) });
    } else if (activeCount < frequencyDays) {
      onChange({
        activeDays: [
          ...data.activeDays,
          { dayIndex, sessionType: "full_body" as const },
        ].sort((a, b) => a.dayIndex - b.dayIndex),
      });
    }
  };

  const updateSessionType = (dayIndex: number, sessionType: SessionType) => {
    onChange({
      activeDays: data.activeDays.map((d) =>
        d.dayIndex === dayIndex ? { ...d, sessionType } : d
      ),
    });
  };

  const remaining = frequencyDays - activeCount;

  return (
    <div className="space-y-6">
      <StepHeader
        title="Weekly Schedule"
        subtitle={`Select exactly ${frequencyDays} training days and assign a session type to each.`}
      />

      <div
        className={`rounded-lg px-4 py-2 text-sm font-medium ${
          remaining === 0
            ? "bg-green-50 text-green-700 dark:bg-green-500/10 dark:text-green-400"
            : "bg-indigo-50 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-400"
        }`}
      >
        {remaining === 0
          ? "All training days selected."
          : `Select ${remaining} more day${remaining !== 1 ? "s" : ""}.`}
      </div>

      <div className="grid grid-cols-7 gap-2">
        {DAY_LABELS.map((label, i) => {
          const active = data.activeDays.some((d) => d.dayIndex === i);
          const canToggle = active || activeCount < frequencyDays;
          return (
            <button
              key={i}
              type="button"
              disabled={!canToggle}
              onClick={() => toggleDay(i)}
              className={`rounded-xl border py-3 text-center text-sm font-semibold transition-all ${
                active
                  ? "border-indigo-600 bg-indigo-600 text-white dark:border-indigo-500 dark:bg-indigo-500"
                  : canToggle
                  ? "border-gray-200 bg-white text-gray-600 hover:border-gray-300 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400"
                  : "cursor-not-allowed border-gray-100 bg-gray-50 text-gray-300 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-700"
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>

      {data.activeDays.length > 0 && (
        <div className="space-y-3">
          <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
            Session Type per Day
          </label>
          {data.activeDays.map((day: ScheduledDay) => (
            <div key={day.dayIndex} className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
              <span className="w-10 text-sm font-semibold text-gray-700 dark:text-slate-300">
                {DAY_LABELS[day.dayIndex]}
              </span>
              <select
                value={day.sessionType}
                onChange={(e) => updateSessionType(day.dayIndex, e.target.value as SessionType)}
                className={selectCls}
              >
                {SESSION_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
