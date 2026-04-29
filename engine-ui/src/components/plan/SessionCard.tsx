import type { ExerciseAlternative, GeneratedSession } from "@/lib/types";
import { BlockRow } from "./BlockRow";

interface SessionCardProps {
  session: GeneratedSession;
  editable?: boolean;
  athleteEquipment?: string[];
  onSwapComplete?: (blockId: string, newExercise: ExerciseAlternative) => void;
}

export function SessionCard({ session, editable, athleteEquipment, onSwapComplete }: SessionCardProps) {
  const fatigue = session.metrics?.fatigue_score ?? 0;
  const pct = Math.min(fatigue / 10, 1) * 100;

  let barColor = "bg-emerald-500";
  if (pct > 70) barColor = "bg-red-500";
  else if (pct > 40) barColor = "bg-amber-500";

  return (
    <div
      className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900"
      data-testid={`session-day-${session.day}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3 dark:border-slate-800">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white">
          Day {session.day}
        </h3>
        <div className="flex gap-1.5">
          {session.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-md bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700 dark:bg-blue-500/15 dark:text-blue-400"
            >
              {tag.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      </div>

      {/* Blocks */}
      <div className="px-4 py-1">
        {session.blocks.map((block) => (
          <BlockRow
            key={block.block_id}
            block={block}
            editable={editable}
            athleteEquipment={athleteEquipment}
            onSwapComplete={onSwapComplete}
          />
        ))}
      </div>

      {/* Fatigue bar */}
      {session.metrics && (
        <div className="border-t border-gray-100 px-4 py-3 dark:border-slate-800" data-testid="session-metrics">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-400 dark:text-slate-500">Fatigue</span>
            <span className="font-mono font-semibold text-gray-600 dark:text-slate-300">
              {fatigue.toFixed(1)}
            </span>
          </div>
          <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-slate-800">
            <div
              className={`h-full rounded-full transition-all ${barColor}`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
