import { useEffect, useState } from 'react';
import { useNavigate, useParams, useLocation, useSearchParams } from 'react-router-dom';
import { getTodayWorkout, logWorkout, getWorkoutDetail } from '../services/templates';
import type { TodayWorkoutResponse, ExerciseLogRequest, SetLogRequest } from '../services/templates';
import { ApiError } from '../services/api';
import styles from './ProgramDayView.module.css';

interface SetDraft {
  actual_reps: string;
  actual_weight_lbs: string;
  actual_rpe: string;
  notes: string;
}

function defaultSets(count: number): SetDraft[] {
  return Array.from({ length: count }, () => ({
    actual_reps: '',
    actual_weight_lbs: '',
    actual_rpe: '',
    notes: '',
  }));
}

export function ProgramDayView() {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const returnTo: string = location.state?.returnTo ?? '/my-programs';
  const previousLogId: string | undefined = location.state?.workout_log_id;
  const targetWeek = searchParams.get('week') ? Number(searchParams.get('week')) : undefined;
  const targetDay = searchParams.get('day') ? Number(searchParams.get('day')) : undefined;

  const [today, setToday] = useState<TodayWorkoutResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Per-exercise set drafts: exerciseId -> SetDraft[]
  const [setDrafts, setSetDrafts] = useState<Record<string, SetDraft[]>>({});
  const [dayStatus, setDayStatus] = useState<'completed' | 'skipped' | 'partial'>('completed');
  const [sessionRating, setSessionRating] = useState<number | ''>('');
  const [notes, setNotes] = useState('');
  const [durationMinutes, setDurationMinutes] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    if (!assignmentId) return;
    const load = async () => {
      try {
        setLoading(true);
        const [data, prevLog] = await Promise.all([
          getTodayWorkout(assignmentId, targetWeek, targetDay),
          previousLogId ? getWorkoutDetail(previousLogId) : Promise.resolve(null),
        ]);
        setToday(data);

        // Build a lookup from program_day_exercise_id → previous sets
        const prevByExId: Record<string, SetDraft[]> = {};
        if (prevLog) {
          for (const exLog of prevLog.exercise_logs) {
            if (exLog.program_day_exercise_id) {
              prevByExId[exLog.program_day_exercise_id] = exLog.sets.map((s) => ({
                actual_reps: s.actual_reps != null ? String(s.actual_reps) : '',
                actual_weight_lbs: s.actual_weight_lbs != null ? String(s.actual_weight_lbs) : '',
                actual_rpe: s.actual_rpe != null ? String(s.actual_rpe) : '',
                notes: s.notes ?? '',
              }));
            }
          }
          // Pre-fill session-level fields
          if (prevLog.day_status) setDayStatus(prevLog.day_status as 'completed' | 'skipped' | 'partial');
          if (prevLog.duration_minutes) setDurationMinutes(prevLog.duration_minutes);
          if (prevLog.session_rating) setSessionRating(prevLog.session_rating);
          if (prevLog.notes) setNotes(prevLog.notes);
        }

        // Initialize set drafts — use previous values if available, else defaults
        const drafts: Record<string, SetDraft[]> = {};
        for (const ex of data.exercises) {
          drafts[ex.id] = prevByExId[ex.id] ?? defaultSets(ex.sets);
        }
        setSetDrafts(drafts);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to load workout';
        setError(msg);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [assignmentId]);

  const updateSet = (exId: string, setIdx: number, field: keyof SetDraft, value: string) => {
    setSetDrafts((prev) => {
      const exSets = [...(prev[exId] ?? [])];
      exSets[setIdx] = { ...exSets[setIdx], [field]: value };
      return { ...prev, [exId]: exSets };
    });
  };

  const handleSubmit = async () => {
    if (!assignmentId || !today) return;
    try {
      setSubmitting(true);
      setSubmitError(null);

      // When skipped, don't send exercise data
      const exerciseLogs: ExerciseLogRequest[] = dayStatus === 'skipped'
        ? []
        : today.exercises.map((ex) => {
          const drafts = setDrafts[ex.id] ?? defaultSets(ex.sets);
          const sets: SetLogRequest[] = drafts.map((d, i) => ({
            set_number: i + 1,
            actual_reps: d.actual_reps ? parseInt(d.actual_reps) : undefined,
            actual_weight_lbs: d.actual_weight_lbs ? parseFloat(d.actual_weight_lbs) : undefined,
            actual_rpe: d.actual_rpe ? parseFloat(d.actual_rpe) : undefined,
            notes: d.notes || undefined,
          }));
          return {
            program_day_exercise_id: ex.id,
            exercise_name: ex.exercise_name,
            sets,
          };
        });

      const res = await logWorkout({
        assignment_id: assignmentId,
        program_day_id: today.program_day_id,
        day_status: dayStatus,
        duration_minutes: durationMinutes || undefined,
        session_rating: sessionRating !== '' ? Number(sessionRating) : undefined,
        notes: notes || undefined,
        exercise_logs: exerciseLogs,
      });

      navigate(returnTo, {
        state: { logged: true, new_week: res.current_week, new_day: res.current_day },
      });
    } catch (err: unknown) {
      let msg = 'Failed to log workout';
      if (err instanceof ApiError) {
        // 422: show human-readable field errors
        const data = err.data as { messages?: string[]; detail?: unknown } | undefined;
        if (err.status === 422 && data?.messages?.length) {
          msg = 'Validation error:\n' + data.messages.join('\n');
        } else {
          msg = typeof err.message === 'string' ? err.message : 'Request failed';
        }
      } else if (err instanceof Error) {
        msg = err.message;
      }
      setSubmitError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className={styles.page}><p>Loading today's workout...</p></div>;
  if (error) return <div className={styles.page}><p className={styles.error}>{error}</p></div>;
  if (!today) return null;

  const healthColor = today.progress_health === 'green' ? '#2e7d32' : today.progress_health === 'yellow' ? '#f57c00' : '#c62828';

  return (
    <div className={styles.page}>
      <button className={styles.back} onClick={() => navigate(returnTo)}>
        ← Back to Plan
      </button>

      <div className={styles.header}>
        <div className={styles.position}>Week {today.current_week} · Day {today.current_day}</div>
        <h1>{today.day_name}</h1>
        <div className={styles.progressRow}>
          <div className={styles.progressBar}>
            <div
              className={styles.progressFill}
              style={{ width: `${today.progress_percentage}%`, background: healthColor }}
            />
          </div>
          <span className={styles.progressPct}>{Math.round(today.progress_percentage)}%</span>
        </div>
      </div>

      {previousLogId && (
        <div className={styles.relogBanner}>
          Editing a previously logged session — values pre-filled from your last entry.
        </div>
      )}

      {/* Status selector — pick outcome BEFORE entering exercise data */}
      <div className={styles.statusSection}>
        <p className={styles.statusLabel}>How did this session go? <span className={styles.required}>*</span></p>
        <div className={styles.statusRow}>
          {(['completed', 'partial', 'skipped'] as const).map((s) => (
            <button
              key={s}
              className={dayStatus === s ? styles.statusActive : styles.statusBtn}
              onClick={() => setDayStatus(s)}
            >
              {s === 'completed' ? 'Completed' : s === 'partial' ? 'Partial' : 'Skipped'}
            </button>
          ))}
        </div>
        {dayStatus === 'skipped' && (
          <p className={styles.skipNote}>No exercise data needed — just add a note if you'd like.</p>
        )}
      </div>

      {/* Exercises — hidden when skipped */}
      {dayStatus !== 'skipped' && (
        <div className={styles.exercises}>
          <p className={styles.sectionHint}>
            All set fields are <strong>optional</strong> — fill in what you tracked.
          </p>
          {today.exercises.map((ex) => (
            <div key={ex.id} className={styles.exerciseCard}>
              <div className={styles.exerciseHeader}>
                <h3>{ex.exercise_name}</h3>
                <span className={styles.prescription}>
                  {ex.sets} × {ex.reps_target ?? ex.reps ?? '?'}
                  {ex.weight_lbs ? ` @ ${ex.weight_lbs} lbs` : ''}
                  {ex.rpe_target ? ` RPE ${ex.rpe_target}` : ''}
                </span>
              </div>
              {ex.coaching_cues && (
                <p className={styles.cues}>{ex.coaching_cues}</p>
              )}

              <div className={styles.setGrid}>
                <div className={styles.setHeader}>
                  <span>Set</span><span>Reps</span><span>Weight (lbs)</span><span>RPE (1–10)</span>
                </div>
                {(setDrafts[ex.id] ?? defaultSets(ex.sets)).map((s, i) => (
                  <div key={i} className={styles.setRow}>
                    <span className={styles.setNum}>{i + 1}</span>
                    <input
                      type="number"
                      className={styles.setInput}
                      placeholder={String(ex.reps_target ?? ex.reps ?? '—')}
                      value={s.actual_reps}
                      onChange={(e) => updateSet(ex.id, i, 'actual_reps', e.target.value)}
                    />
                    <input
                      type="number"
                      className={styles.setInput}
                      placeholder={ex.weight_lbs ? String(ex.weight_lbs) : '—'}
                      value={s.actual_weight_lbs}
                      onChange={(e) => updateSet(ex.id, i, 'actual_weight_lbs', e.target.value)}
                    />
                    <input
                      type="number"
                      className={styles.setInput}
                      placeholder={ex.rpe_target ? String(ex.rpe_target) : '—'}
                      min="1"
                      max="10"
                      step="0.5"
                      value={s.actual_rpe}
                      onChange={(e) => updateSet(ex.id, i, 'actual_rpe', e.target.value)}
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Session summary */}
      <div className={styles.summary}>
        <h2>Session Details</h2>

        {dayStatus !== 'skipped' && (
          <>
            <label className={styles.label}>
              Duration (minutes) <span className={styles.optional}>(optional)</span>
              <input
                type="number"
                className={styles.input}
                placeholder="e.g. 60"
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(e.target.value)}
              />
            </label>

            <label className={styles.label}>
              Session rating (1–5) <span className={styles.optional}>(optional)</span>
              <input
                type="number"
                className={styles.input}
                min="1"
                max="5"
                placeholder="1–5"
                value={sessionRating}
                onChange={(e) => setSessionRating(e.target.value === '' ? '' : Number(e.target.value))}
              />
            </label>
          </>
        )}

        <label className={styles.label}>
          Notes <span className={styles.optional}>(optional)</span>
          <textarea
            className={styles.textarea}
            rows={3}
            placeholder={dayStatus === 'skipped' ? 'Why did you skip? (optional)' : 'How did it feel? Any modifications?'}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </label>

        {submitError && <p className={styles.error} style={{ whiteSpace: 'pre-line' }}>{submitError}</p>}

        <button
          className={styles.submitBtn}
          onClick={handleSubmit}
          disabled={submitting}
        >
          {submitting ? 'Saving...' : dayStatus === 'skipped' ? 'Log as Skipped' : 'Log Workout'}
        </button>
      </div>
    </div>
  );
}
