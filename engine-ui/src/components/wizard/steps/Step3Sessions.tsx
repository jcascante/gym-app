import { StepHeader } from "../shared/StepHeader";
import type { Step2Data, Step3Data, Block, BlockType, ExerciseCategory, SessionDef } from "@/lib/wizard/types";

interface Props {
  data: Step3Data;
  schedule: Step2Data;
  onChange: (data: Step3Data) => void;
}

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const BLOCK_TYPES: { value: BlockType; label: string }[] = [
  { value: "main_lift", label: "Main Lift" },
  { value: "accessory", label: "Accessory" },
  { value: "conditioning", label: "Conditioning" },
];

const EXERCISE_CATEGORIES: { value: ExerciseCategory; label: string }[] = [
  { value: "squat", label: "Squat" },
  { value: "hip_hinge", label: "Hip Hinge" },
  { value: "horizontal_push", label: "Horizontal Push" },
  { value: "horizontal_pull", label: "Horizontal Pull" },
  { value: "vertical_push", label: "Vertical Push" },
  { value: "vertical_pull", label: "Vertical Pull" },
  { value: "core", label: "Core" },
  { value: "conditioning", label: "Conditioning" },
];

const selectCls =
  "rounded-lg border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900 outline-none focus:border-indigo-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100";

function BlockRow({
  block,
  onChange,
  onRemove,
}: {
  block: Block;
  onChange: (b: Block) => void;
  onRemove: () => void;
}) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 p-2 dark:border-slate-700 dark:bg-slate-800/50">
      <select
        value={block.blockType}
        onChange={(e) => onChange({ ...block, blockType: e.target.value as BlockType })}
        className={selectCls}
      >
        {BLOCK_TYPES.map((t) => (
          <option key={t.value} value={t.value}>
            {t.label}
          </option>
        ))}
      </select>
      <span className="text-xs text-gray-400">·</span>
      <select
        value={block.exerciseCategory}
        onChange={(e) => onChange({ ...block, exerciseCategory: e.target.value as ExerciseCategory })}
        className={`${selectCls} flex-1`}
      >
        {EXERCISE_CATEGORIES.map((c) => (
          <option key={c.value} value={c.value}>
            {c.label}
          </option>
        ))}
      </select>
      <button
        type="button"
        onClick={onRemove}
        className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-500/10"
        aria-label="Remove block"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

export function Step3Sessions({ data, schedule, onChange }: Props) {
  const updateSession = (dayIndex: number, session: SessionDef) => {
    onChange({
      sessions: data.sessions.map((s) => (s.dayIndex === dayIndex ? session : s)),
    });
  };

  const addBlock = (dayIndex: number) => {
    const session = data.sessions.find((s) => s.dayIndex === dayIndex);
    if (!session) return;
    const newBlock: Block = {
      id: `s${dayIndex}_b${Date.now()}`,
      blockType: "accessory",
      exerciseCategory: "horizontal_push",
    };
    updateSession(dayIndex, { ...session, blocks: [...session.blocks, newBlock] });
  };

  const updateBlock = (dayIndex: number, blockId: string, block: Block) => {
    const session = data.sessions.find((s) => s.dayIndex === dayIndex);
    if (!session) return;
    updateSession(dayIndex, {
      ...session,
      blocks: session.blocks.map((b) => (b.id === blockId ? block : b)),
    });
  };

  const removeBlock = (dayIndex: number, blockId: string) => {
    const session = data.sessions.find((s) => s.dayIndex === dayIndex);
    if (!session) return;
    updateSession(dayIndex, {
      ...session,
      blocks: session.blocks.filter((b) => b.id !== blockId),
    });
  };

  return (
    <div className="space-y-6">
      <StepHeader
        title="Session Structure"
        subtitle="Add training blocks to each session. Each block targets an exercise category."
      />

      <div className="space-y-4">
        {schedule.activeDays.map((scheduledDay) => {
          const session = data.sessions.find((s) => s.dayIndex === scheduledDay.dayIndex);
          if (!session) return null;
          const hasBlocks = session.blocks.length > 0;

          return (
            <div
              key={scheduledDay.dayIndex}
              className="rounded-xl border border-gray-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900"
            >
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <span className="text-sm font-bold text-gray-900 dark:text-white">
                    {DAY_LABELS[scheduledDay.dayIndex]}
                  </span>
                  <span className="ml-2 text-xs text-gray-500 dark:text-slate-400 capitalize">
                    {scheduledDay.sessionType.replace(/_/g, " ")}
                  </span>
                </div>
                {!hasBlocks && (
                  <span className="text-xs text-amber-600 dark:text-amber-400">
                    Add at least 1 block
                  </span>
                )}
              </div>

              <div className="space-y-2">
                {session.blocks.map((block) => (
                  <BlockRow
                    key={block.id}
                    block={block}
                    onChange={(b) => updateBlock(scheduledDay.dayIndex, block.id, b)}
                    onRemove={() => removeBlock(scheduledDay.dayIndex, block.id)}
                  />
                ))}
              </div>

              <button
                type="button"
                onClick={() => addBlock(scheduledDay.dayIndex)}
                className="mt-2 flex items-center gap-1.5 rounded-lg border border-dashed border-gray-300 px-3 py-1.5 text-xs text-gray-500 transition-colors hover:border-indigo-400 hover:text-indigo-600 dark:border-slate-600 dark:hover:border-indigo-500 dark:hover:text-indigo-400"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 5v14M5 12h14" />
                </svg>
                Add block
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
