import { useState } from 'react';
import type { GeneratedPlan, EngineBlock } from '../types/engine';
import PrescriptionCard from './PrescriptionCard';
import ExerciseSwapModal from './ExerciseSwapModal';
import './GeneratedPlanView.css';

const DAY_NAMES = ['', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const BLOCK_TYPE_LABELS: Record<string, string> = {
  main_lift: 'Main',
  secondary_lift: 'Secondary',
  accessory: 'Accessory',
  conditioning_steady: 'Cardio',
  conditioning_intervals: 'HIIT',
  circuit: 'Circuit',
  mobility: 'Mobility',
  warmup: 'Warm-up',
  cooldown: 'Cool-down',
};

interface Props {
  plan: GeneratedPlan;
  editable?: boolean;
  onPlanUpdated?: (plan: GeneratedPlan) => void;
}

export default function GeneratedPlanView({ plan, editable = false, onPlanUpdated }: Props) {
  const [activeWeek, setActiveWeek] = useState(0);
  const [swapBlock, setSwapBlock] = useState<EngineBlock | null>(null);

  const athleteEquipment = (() => {
    const echo = plan.inputs_echo as Record<string, unknown>;
    const athlete = echo?.athlete as Record<string, unknown> | undefined;
    return (athlete?.equipment as string[]) ?? [];
  })();

  const week = plan.weeks[activeWeek];

  return (
    <div className="gpv-root">
      {/* Week tabs */}
      <div className="gpv-week-tabs">
        {plan.weeks.map((w, i) => (
          <button
            key={w.week}
            className={`gpv-week-tab ${i === activeWeek ? 'active' : ''}`}
            onClick={() => setActiveWeek(i)}
          >
            Week {w.week}
          </button>
        ))}
      </div>

      {/* Sessions */}
      <div className="gpv-sessions">
        {week.sessions.map(session => (
          <div key={session.day} className="gpv-session">
            <div className="gpv-session-header">
              <span className="gpv-day">{DAY_NAMES[session.day] ?? `Day ${session.day}`}</span>
              <div className="gpv-tags">
                {session.tags.map(t => (
                  <span key={t} className="gpv-tag">{t.replace(/_/g, ' ')}</span>
                ))}
              </div>
              {session.metrics?.fatigue_score != null && (
                <span className="gpv-fatigue" title="Fatigue score">
                  ⚡ {session.metrics.fatigue_score.toFixed(1)}
                </span>
              )}
            </div>

            <div className="gpv-blocks">
              {session.blocks.map(block => (
                <div key={block.block_id} className="gpv-block">
                  <div className="gpv-block-header">
                    <span className={`gpv-block-type type-${block.type}`}>
                      {BLOCK_TYPE_LABELS[block.type] ?? block.type}
                    </span>
                    <span className="gpv-exercise-name">{block.exercise.name}</span>
                    {editable && (
                      <button
                        className="gpv-swap-btn"
                        onClick={() => setSwapBlock(block)}
                      >
                        Swap
                      </button>
                    )}
                  </div>
                  <PrescriptionCard prescription={block.prescription} />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {plan.warnings.length > 0 && (
        <div className="gpv-warnings">
          {plan.warnings.map((w, i) => <p key={i}>⚠️ {w}</p>)}
        </div>
      )}

      {swapBlock && (
        <ExerciseSwapModal
          isOpen={true}
          block={swapBlock}
          athleteEquipment={athleteEquipment}
          currentPlan={plan}
          onApplySwap={updated => {
            onPlanUpdated?.(updated);
            setSwapBlock(null);
          }}
          onClose={() => setSwapBlock(null)}
        />
      )}
    </div>
  );
}
