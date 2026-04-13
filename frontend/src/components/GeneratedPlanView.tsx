import { useState } from 'react';
import type { GeneratedPlan, EngineBlock } from '../types/engine';
import type { AssignmentState } from '../services/templates';
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

type SessionStatus = 'logged' | 'next' | 'upcoming';

/** Derive per-session status from assignment progress.
 *  current_week/current_day = the NEXT session to log (1-based).
 *  Sessions before that position are already logged. */
function getSessionStatus(
  weekNumber: number,
  sessionIndex: number,   // 0-based position within the week's sessions
  assignment: AssignmentState | null,
): SessionStatus {
  if (!assignment) return 'upcoming';
  const { current_week, current_day } = assignment;
  const sessionDay = sessionIndex + 1; // convert to 1-based

  if (weekNumber < current_week) return 'logged';
  if (weekNumber === current_week) {
    if (sessionDay < current_day) return 'logged';
    if (sessionDay === current_day) return 'next';
  }
  return 'upcoming';
}

interface Props {
  plan: GeneratedPlan;
  editable?: boolean;
  onPlanUpdated?: (plan: GeneratedPlan) => void;
  assignment?: AssignmentState | null;
}

function sessionKey(weekNumber: number, sessionIdx: number) {
  return `${weekNumber}-${sessionIdx}`;
}

export default function GeneratedPlanView({ plan, editable = false, onPlanUpdated, assignment = null }: Props) {
  // Default to the current week tab when an assignment is active
  const defaultWeekIdx = assignment
    ? Math.max(0, Math.min(assignment.current_week - 1, plan.weeks.length - 1))
    : 0;
  const [activeWeek, setActiveWeek] = useState(defaultWeekIdx);
  const [swapBlock, setSwapBlock] = useState<EngineBlock | null>(null);

  // Collapsed sessions: default logged ones to collapsed
  const [collapsed, setCollapsed] = useState<Set<string>>(() => {
    const initial = new Set<string>();
    plan.weeks.forEach((w) => {
      w.sessions.forEach((_, si) => {
        if (getSessionStatus(w.week, si, assignment) === 'logged') {
          initial.add(sessionKey(w.week, si));
        }
      });
    });
    return initial;
  });

  const toggleCollapsed = (key: string) => {
    setCollapsed(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const athleteEquipment = (() => {
    const echo = plan.inputs_echo as Record<string, unknown>;
    const athlete = echo?.athlete as Record<string, unknown> | undefined;
    return (athlete?.equipment as string[]) ?? [];
  })();

  const week = plan.weeks[activeWeek];

  // Is the entire displayed week fully logged?
  const weekFullyLogged = assignment && week.sessions.every((_, i) =>
    getSessionStatus(week.week, i, assignment) === 'logged'
  );

  return (
    <div className="gpv-root">
      {/* Week tabs */}
      <div className="gpv-week-tabs">
        {plan.weeks.map((w, i) => {
          const allLogged = assignment && w.sessions.every((_, si) =>
            getSessionStatus(w.week, si, assignment) === 'logged'
          );
          return (
            <button
              key={w.week}
              className={`gpv-week-tab ${i === activeWeek ? 'active' : ''} ${allLogged ? 'logged' : ''}`}
              onClick={() => setActiveWeek(i)}
            >
              Week {w.week}{allLogged ? ' ✓' : ''}
            </button>
          );
        })}
      </div>

      {weekFullyLogged && (
        <p className="gpv-week-done-note">All sessions in this week have been logged.</p>
      )}

      {/* Sessions */}
      <div className="gpv-sessions">
        {week.sessions.map((session, sessionIdx) => {
          const status = getSessionStatus(week.week, sessionIdx, assignment);
          const key = sessionKey(week.week, sessionIdx);
          const isCollapsed = collapsed.has(key);
          return (
            <div key={session.day} className={`gpv-session ${status === 'logged' ? 'gpv-session-logged' : status === 'next' ? 'gpv-session-next' : ''}`}>
              <button
                className="gpv-session-header gpv-session-toggle"
                onClick={() => toggleCollapsed(key)}
                aria-expanded={!isCollapsed}
              >
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
                {status === 'logged' && (
                  <span className="gpv-status-badge gpv-badge-logged">Logged</span>
                )}
                {status === 'next' && (
                  <span className="gpv-status-badge gpv-badge-next">Next up</span>
                )}
                <span className={`gpv-chevron ${isCollapsed ? 'gpv-chevron-collapsed' : ''}`}>▾</span>
              </button>

              {!isCollapsed && (
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
                            onClick={(e) => { e.stopPropagation(); setSwapBlock(block); }}
                          >
                            Swap
                          </button>
                        )}
                      </div>
                      <PrescriptionCard prescription={block.prescription} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
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
