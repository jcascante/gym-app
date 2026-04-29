import { StepHeader } from "../shared/StepHeader";
import { CardSelect, PillSelect } from "../shared/CardSelect";
import type { Step1Data, ProgramType, DurationWeeks, FrequencyDays } from "@/lib/wizard/types";

interface Props {
  data: Step1Data;
  onChange: (data: Step1Data) => void;
}

const PROGRAM_TYPE_OPTIONS: { value: ProgramType; label: string; description: string }[] = [
  { value: "strength", label: "Strength", description: "Low reps, high load, percentage-based" },
  { value: "hypertrophy", label: "Hypertrophy", description: "Moderate reps, volume focus" },
  { value: "conditioning", label: "Conditioning", description: "Cardio & endurance work" },
];

const DURATION_OPTIONS: { value: DurationWeeks; label: string }[] = [
  { value: 4, label: "4 weeks" },
  { value: 6, label: "6 weeks" },
  { value: 8, label: "8 weeks" },
  { value: 12, label: "12 weeks" },
];

const FREQUENCY_OPTIONS: { value: FrequencyDays; label: string }[] = [
  { value: 3, label: "3 days/wk" },
  { value: 4, label: "4 days/wk" },
  { value: 5, label: "5 days/wk" },
];

const inputCls =
  "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none transition-colors focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:focus:border-indigo-400";

export function Step1Basics({ data, onChange }: Props) {
  const set = <K extends keyof Step1Data>(key: K, value: Step1Data[K]) =>
    onChange({ ...data, [key]: value });

  return (
    <div className="space-y-6">
      <StepHeader
        title="Program Basics"
        subtitle="Give your program a name and define the overall structure."
      />

      <div className="space-y-1">
        <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
          Program Name *
        </label>
        <input
          type="text"
          value={data.name}
          onChange={(e) => set("name", e.target.value)}
          placeholder="e.g. 12-Week Strength Block"
          className={inputCls}
        />
      </div>

      <div className="space-y-1">
        <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
          Description
        </label>
        <textarea
          value={data.description}
          onChange={(e) => set("description", e.target.value)}
          placeholder="Brief description of the program goals..."
          rows={2}
          className={`${inputCls} resize-none`}
        />
      </div>

      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
          Program Type
        </label>
        <CardSelect
          options={PROGRAM_TYPE_OPTIONS}
          value={data.programType}
          onChange={(v) => set("programType", v)}
          columns={3}
        />
      </div>

      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
          Duration
        </label>
        <PillSelect
          options={DURATION_OPTIONS}
          value={data.durationWeeks}
          onChange={(v) => set("durationWeeks", v)}
        />
      </div>

      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
          Training Frequency
        </label>
        <PillSelect
          options={FREQUENCY_OPTIONS}
          value={data.frequencyDays}
          onChange={(v) => set("frequencyDays", v)}
        />
      </div>
    </div>
  );
}
