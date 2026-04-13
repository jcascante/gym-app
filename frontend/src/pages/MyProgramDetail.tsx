import { useEffect, useState } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { getAssignment, getProgramDetail, getAssignmentLogs } from '../services/templates';
import type { AssignmentState, ProgramDetail, DayLogSummary } from '../services/templates';
import styles from './MyProgramDetail.module.css';

function healthColor(health: string) {
  if (health === 'green') return '#2e7d32';
  if (health === 'yellow') return '#f57c00';
  return '#c62828';
}

type DayStatus = 'completed' | 'partial' | 'skipped' | 'current' | 'missed' | 'upcoming';

function getDayStatus(
  weekNum: number,
  dayNum: number,
  assignment: AssignmentState,
  logsByDayId: Map<string, DayLogSummary>,
  dayId: string,
): DayStatus {
  const log = logsByDayId.get(dayId);
  if (log) {
    return log.day_status as DayStatus;
  }
  const isCurrent = weekNum === assignment.current_week && dayNum === assignment.current_day;
  if (isCurrent) return 'current';
  const isPast =
    weekNum < assignment.current_week ||
    (weekNum === assignment.current_week && dayNum < assignment.current_day);
  if (isPast) return 'missed';
  return 'upcoming';
}

const STATUS_LABEL: Record<DayStatus, string> = {
  completed: 'Done',
  partial: 'Partial',
  skipped: 'Skipped',
  current: 'Up next',
  missed: 'Missed',
  upcoming: '',
};

const STATUS_COLOR: Record<DayStatus, string> = {
  completed: '#2e7d32',
  partial: '#1565c0',
  skipped: '#757575',
  current: '#e65100',
  missed: '#c62828',
  upcoming: '#bdbdbd',
};

export function MyProgramDetail() {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const navigate = useNavigate();
  const location = useLocation();

  const [assignment, setAssignment] = useState<AssignmentState | null>(null);
  const [program, setProgram] = useState<ProgramDetail | null>(null);
  const [logsByDayId, setLogsByDayId] = useState<Map<string, DayLogSummary>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedWeeks, setExpandedWeeks] = useState<Set<number>>(new Set());

  async function load(id: string) {
    setLoading(true);
    setError(null);
    try {
      const a = await getAssignment(id);
      const [p, logs] = await Promise.all([
        getProgramDetail(a.program_id),
        getAssignmentLogs(id),
      ]);
      setAssignment(a);
      setProgram(p);
      const map = new Map<string, DayLogSummary>();
      for (const log of logs) {
        if (log.program_day_id) map.set(log.program_day_id, log);
      }
      setLogsByDayId(map);
      // Auto-expand current week
      setExpandedWeeks(new Set([a.current_week]));
    } catch {
      setError('Program not found');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!assignmentId) return;
    load(assignmentId);
  }, [assignmentId]);

  useEffect(() => {
    if (location.state?.logged && assignmentId) {
      load(assignmentId);
    }
  }, [location.state]);

  function toggleWeek(weekNum: number) {
    setExpandedWeeks(prev => {
      const next = new Set(prev);
      if (next.has(weekNum)) next.delete(weekNum);
      else next.add(weekNum);
      return next;
    });
  }

  if (loading) return <div className={styles.page}><p>Loading...</p></div>;
  if (error || !assignment || !program) {
    return (
      <div className={styles.page}>
        <p className={styles.error}>{error ?? 'Program not found'}</p>
        <button className={styles.back} onClick={() => navigate('/my-programs')}>← My Programs</button>
      </div>
    );
  }

  const pct = Math.round(assignment.progress_percentage);
  const color = healthColor(assignment.progress_health);
  const isActive = assignment.status !== 'completed' && assignment.status !== 'cancelled';

  return (
    <div className={styles.page}>
      <button className={styles.back} onClick={() => navigate('/my-programs')}>
        ← My Programs
      </button>

      <div className={styles.header}>
        <h1>{assignment.assignment_name || program.name}</h1>
        <div className={styles.meta}>
          <span>Started {new Date(assignment.start_date).toLocaleDateString()}</span>
          {assignment.end_date && (
            <span>· Ends {new Date(assignment.end_date).toLocaleDateString()}</span>
          )}
          <span>· {program.duration_weeks}w · {program.days_per_week}d/w</span>
        </div>
      </div>

      {/* Progress summary */}
      <div className={styles.progressPanel}>
        <div className={styles.progressTop}>
          <div>
            <div className={styles.position}>
              Week {assignment.current_week} · Day {assignment.current_day}
            </div>
            <div className={styles.counts}>
              <span>{assignment.workouts_completed} completed</span>
              <span>{assignment.workouts_skipped} skipped</span>
            </div>
          </div>
          <div className={styles.progressRight}>
            <span className={styles.pct} style={{ color }}>{pct}%</span>
            {isActive && (
              <button
                className={styles.logBtn}
                onClick={() => navigate(`/log/${assignmentId}`, {
                  state: { returnTo: `/my-programs/${assignmentId}` },
                })}
              >
                Log Today's Workout
              </button>
            )}
          </div>
        </div>
        <div className={styles.barWrap}>
          <div className={styles.bar}>
            <div className={styles.fill} style={{ width: `${pct}%`, background: color }} />
          </div>
        </div>
      </div>

      {assignment.status === 'completed' && (
        <div className={styles.completedBanner}>Program complete! Great work.</div>
      )}

      {/* Full program structure */}
      <div className={styles.weeks}>
        {program.weeks.map((week) => {
          const isExpanded = expandedWeeks.has(week.week_number);
          const isCurrent = week.week_number === assignment.current_week;
          return (
            <div key={week.week_number} className={styles.weekBlock}>
              <button
                className={`${styles.weekHeader} ${isCurrent ? styles.weekCurrent : ''}`}
                onClick={() => toggleWeek(week.week_number)}
              >
                <span className={styles.weekTitle}>
                  Week {week.week_number}
                  {week.name && !/^week\s*\d+$/i.test(week.name.trim()) ? ` — ${week.name}` : ''}
                  {isCurrent && <span className={styles.currentBadge}>Current</span>}
                </span>
                <span className={styles.chevron}>{isExpanded ? '▲' : '▼'}</span>
              </button>

              {isExpanded && (
                <div className={styles.days}>
                  {week.days.map((day) => {
                    const dayStatus = getDayStatus(
                      week.week_number,
                      day.day_number,
                      assignment,
                      logsByDayId,
                      day.id,
                    );
                    const statusColor = STATUS_COLOR[dayStatus];
                    const canLog = isActive && dayStatus !== 'upcoming';

                    return (
                      <div key={day.day_number} className={styles.dayRow}>
                        <div className={styles.dayInfo}>
                          <div className={styles.dayName}>
                            Day {day.day_number}{day.name && !/^day\s*\d+$/i.test(day.name.trim()) ? ` — ${day.name}` : ''}
                          </div>
                          <div className={styles.exercises}>
                            {day.exercises.map((ex, i) => (
                              <span key={i} className={styles.exChip}>
                                {ex.exercise_name} {ex.sets}×{ex.reps}
                                {ex.weight_lbs ? ` @ ${ex.weight_lbs}lbs` : ''}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div className={styles.dayActions}>
                          {STATUS_LABEL[dayStatus] && (
                            <span className={styles.statusBadge} style={{ color: statusColor }}>
                              {STATUS_LABEL[dayStatus]}
                            </span>
                          )}
                          {canLog && (
                            <button
                              className={styles.dayLogBtn}
                              onClick={() => {
                                const existingLog = logsByDayId.get(day.id);
                                navigate(
                                  `/log/${assignmentId}?week=${week.week_number}&day=${day.day_number}`,
                                  {
                                    state: {
                                      returnTo: `/my-programs/${assignmentId}`,
                                      workout_log_id: existingLog?.workout_log_id,
                                    },
                                  },
                                );
                              }}
                            >
                              {dayStatus === 'completed' || dayStatus === 'partial' || dayStatus === 'skipped'
                                ? 'Re-log'
                                : 'Log'}
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
