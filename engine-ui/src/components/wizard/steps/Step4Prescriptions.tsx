import { StepHeader } from "../shared/StepHeader";
import { PillSelect } from "../shared/CardSelect";
import type {
  Step3Data,
  Step4Data,
  BlockPrescription,
  TrainingStyle,
  RepRange,
  IntensityLevel,
  ProgressionPattern,
} from "@/lib/wizard/types";

interface Props {
  data: Step4Data;
  sessions: Step3Data;
  onChange: (data: Step4Data) => void;
}

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const STYLE_OPTIONS: { value: TrainingStyle; label: string; description: string }[] = [
  { value: "top_set_plus_backoff", label: "Top Set + Backoff", description: "1 heavy set, then lighter sets" },
  { value: "reps_range_rir", label: "Reps in Range", description: "RIR-based sets across a rep range" },
  { value: "steady_state", label: "Steady State", description: "Constant-pace cardio / conditioning" },
];

const REP_RANGE_OPTIONS: { value: RepRange; label: string }[] = [
  { value: "heavy", label: "Heavy (3–5)" },
  { value: "moderate", label: "Moderate (6–10)" },
  { value: "light", label: "Light (12–15)" },
];

const INTENSITY_OPTIONS: { value: IntensityLevel; label: string }[] = [
  { value: "easy", label: "Easy (RPE 6)" },
  { value: "moderate", label: "Moderate (RPE 7.5)" },
  { value: "hard", label: "Hard (RPE 9)" },
];

const PROGRESSION_OPTIONS: { value: ProgressionPattern; label: string }[] = [
  { value: "linear", label: "Linear" },
  { value: "undulating", label: "Undulating" },
  { value: "fixed", label: "Fixed" },
];

const inputCls =
  "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-indigo-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100";

function BlockEditor({
  rx,
  blockLabel,
  onChange,
}: {
  rx: BlockPrescription;
  blockLabel: string;
  onChange: (rx: BlockPrescription) => void;
}) {
  const set = <K extends keyof BlockPrescription>(k: K, v: BlockPrescription[K]) =>
    onChange({ ...rx, [k]: v });

  const isSteadyState = rx.trainingStyle === "steady_state";

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
      <div className="mb-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
          Block
        </p>
        <p className="text-sm font-bold text-gray-900 dark:text-white">{blockLabel}</p>
      </div>

      <div className="space-y-4">
        <div className="space-y-1.5">
          <label className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
            Training Style
          </label>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            {STYLE_OPTIONS.map((opt) => {
              const active = opt.value === rx.trainingStyle;
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => set("trainingStyle", opt.value)}
                  className={`rounded-lg border px-3 py-2 text-left text-xs transition-all ${
                    active
                      ? "border-indigo-600 bg-indigo-50 dark:border-indigo-500 dark:bg-indigo-500/10"
                      : "border-gray-200 hover:border-gray-300 dark:border-slate-700"
                  }`}
                >
                  <div className={`font-semibold ${active ? "text-indigo-700 dark:text-indigo-400" : "text-gray-900 dark:text-white"}`}>
                    {opt.label}
                  </div>
                  <div className="text-gray-500 dark:text-slate-400">{opt.description}</div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <div className="space-y-1">
            <label className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
              Sets
            </label>
            <input
              type="number"
              min={1}
              max={10}
              value={rx.sets}
              onChange={(e) => set("sets", +e.target.value)}
              className={inputCls}
            />
          </div>

          {!isSteadyState && (
            <>
              <div className="col-span-2 space-y-1.5 sm:col-span-1">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
                  Rep Range
                </label>
                <PillSelect
                  options={REP_RANGE_OPTIONS}
                  value={rx.repRange}
                  onChange={(v) => set("repRange", v)}
                />
              </div>

              <div className="col-span-2 space-y-1.5 sm:col-span-3">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
                  Intensity
                </label>
                <PillSelect
                  options={INTENSITY_OPTIONS}
                  value={rx.intensityLevel}
                  onChange={(v) => set("intensityLevel", v)}
                />
              </div>

              <div className="col-span-2 space-y-1.5 sm:col-span-3">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
                  Progression
                </label>
                <PillSelect
                  options={PROGRESSION_OPTIONS}
                  value={rx.progression}
                  onChange={(v) => set("progression", v)}
                />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export function Step4Prescriptions({ data, sessions, onChange }: Props) {
  const updateRx = (blockId: string, rx: BlockPrescription) => {
    onChange({
      prescriptions: data.prescriptions.map((p) => (p.blockId === blockId ? rx : p)),
    });
  };

  return (
    <div className="space-y-6">
      <StepHeader
        title="Prescriptions"
        subtitle="Configure sets, reps, intensity, and progression for each block."
      />

      {sessions.sessions.map((session) => (
        <div key={session.dayIndex}>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-slate-500">
            {DAY_LABELS[session.dayIndex]} — {session.sessionType.replace(/_/g, " ")}
          </p>
          <div className="space-y-3">
            {session.blocks.map((block) => {
              const rx = data.prescriptions.find((p) => p.blockId === block.id);
              if (!rx) return null;
              const label = `${block.blockType.replace(/_/g, " ")} · ${block.exerciseCategory.replace(/_/g, " ")}`;
              return (
                <BlockEditor
                  key={block.id}
                  rx={rx}
                  blockLabel={label}
                  onChange={(updated) => updateRx(block.id, updated)}
                />
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
