import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getAssignmentWorkouts, createWorkout, updateWorkout, deleteWorkout } from '../services/workouts';
import type { WorkoutLog } from '../services/workouts';
import { ApiError } from '../services/api';
import { getMyPrograms } from '../services/programAssignments';
import type { ProgramAssignmentSummary } from '../services/programAssignments';
import { getProgramDetail } from '../services/programs';
import type { ProgramDetail, DayDetail } from '../services/programs';
import './ProgramDetails.css';

interface LogWorkoutFormState {
  status: 'completed' | 'skipped';
  duration_minutes: string;
  notes: string;
  workout_date: string;
}

function todayISO() {
  return new Date().toISOString().split('T')[0];
}

export default function ProgramDetails() {
  const { assignmentId } = useParams();
  const navigate = useNavigate();

  const [assignment, setAssignment] = useState<ProgramAssignmentSummary | null>(null);
  const [program, setProgram] = useState<ProgramDetail | null>(null);
  const [workouts, setWorkouts] = useState<WorkoutLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Workout log modal state
  const [showLogModal, setShowLogModal] = useState(false);
  const [logForm, setLogForm] = useState<LogWorkoutFormState>({
    status: 'completed',
    duration_minutes: '',
    notes: '',
    workout_date: todayISO(),
  });
  const [submitting, setSubmitting] = useState(false);
  const [logError, setLogError] = useState<string | null>(null);

  // Edit / delete state
  const [editingWorkout, setEditingWorkout] = useState<WorkoutLog | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    if (assignmentId) load();
  }, [assignmentId]);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const myPrograms = await getMyPrograms();
      const found = myPrograms.programs.find(
        (p) => String(p.assignment_id) === String(assignmentId)
      );
      if (found) {
        setAssignment(found);
        // Load full program structure
        const detail = await getProgramDetail(found.program_id);
        setProgram(detail);
      }
      const ws = await getAssignmentWorkouts(assignmentId as string);
      setWorkouts(ws || []);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load program details');
      }
    } finally {
      setLoading(false);
    }
  };

  // Derive the current day's exercises from program structure
  const getCurrentDayPlan = (): DayDetail | null => {
    if (!program || !assignment) return null;
    const week = program.weeks.find((w) => w.week_number === assignment.current_week);
    if (!week) return null;
    return week.days.find((d) => d.day_number === assignment.current_day) ?? null;
  };

  const openLogModal = (existing?: WorkoutLog) => {
    if (existing) {
      setEditingWorkout(existing);
      setLogForm({
        status: existing.status === 'skipped' ? 'skipped' : 'completed',
        duration_minutes: existing.duration_minutes ?? '',
        notes: existing.notes ?? '',
        workout_date: existing.workout_date.split('T')[0],
      });
    } else {
      setEditingWorkout(null);
      setLogForm({
        status: 'completed',
        duration_minutes: '',
        notes: '',
        workout_date: todayISO(),
      });
    }
    setLogError(null);
    setShowLogModal(true);
  };

  const handleLogSubmit = async () => {
    if (!assignment) return;
    setSubmitting(true);
    setLogError(null);
    try {
      const dateTime = new Date(logForm.workout_date + 'T12:00:00').toISOString();
      if (editingWorkout) {
        const updated = await updateWorkout(
          editingWorkout.id,
          logForm.status,
          logForm.duration_minutes || undefined,
          logForm.notes || undefined
        );
        setWorkouts((prev) => prev.map((w) => (w.id === updated.id ? updated : w)));
      } else {
        const created = await createWorkout(
          assignment.assignment_id,
          logForm.status,
          logForm.duration_minutes || undefined,
          logForm.notes || undefined,
          dateTime
        );
        setWorkouts((prev) => [created, ...prev]);
      }
      setShowLogModal(false);
    } catch (err) {
      if (err instanceof ApiError) {
        setLogError(err.message);
      } else {
        setLogError('Failed to save workout. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (workoutId: string) => {
    if (!confirm('Delete this workout log?')) return;
    setDeletingId(workoutId);
    try {
      await deleteWorkout(workoutId);
      setWorkouts((prev) => prev.filter((w) => w.id !== workoutId));
    } catch {
      alert('Failed to delete workout.');
    } finally {
      setDeletingId(null);
    }
  };

  const currentDayPlan = getCurrentDayPlan();
  const completedCount = workouts.filter((w) => w.status === 'completed').length;
  const totalPlanned =
    assignment ? assignment.duration_weeks * assignment.days_per_week : 0;
  const progressPct = totalPlanned > 0 ? Math.round((completedCount / totalPlanned) * 100) : 0;

  return (
    <div className="pd-page">
      {/* ── Header ── */}
      <div className="pd-header">
        <button className="pd-back-btn" onClick={() => navigate(-1)}>
          &#8592; Back
        </button>
        <div className="pd-header-info">
          <h1>{assignment?.program_name ?? 'Program Details'}</h1>
          {assignment?.assignment_name && (
            <p className="pd-assignment-name">{assignment.assignment_name}</p>
          )}
        </div>
        <button className="btn-primary pd-log-btn" onClick={() => openLogModal()}>
          Log Workout
        </button>
      </div>

      {loading ? (
        <div className="pd-loading">
          <div className="spinner" />
          <span>Loading…</span>
        </div>
      ) : error ? (
        <div className="pd-error">{error}</div>
      ) : (
        <div className="pd-body">
          {/* ── Stats bar ── */}
          <div className="pd-stats-bar">
            <div className="pd-stat">
              <span className="pd-stat-value">{assignment?.duration_weeks ?? '-'}</span>
              <span className="pd-stat-label">Weeks</span>
            </div>
            <div className="pd-stat">
              <span className="pd-stat-value">{assignment?.days_per_week ?? '-'}</span>
              <span className="pd-stat-label">Days / wk</span>
            </div>
            <div className="pd-stat">
              <span className="pd-stat-value">{completedCount}</span>
              <span className="pd-stat-label">Completed</span>
            </div>
            <div className="pd-stat">
              <span className="pd-stat-value">{progressPct}%</span>
              <span className="pd-stat-label">Progress</span>
            </div>
          </div>

          {/* ── Progress bar ── */}
          <div className="pd-progress-wrap">
            <div
              className="pd-progress-bar"
              style={{ width: `${progressPct}%` }}
              role="progressbar"
              aria-valuenow={progressPct}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>

          {/* ── Current day plan ── */}
          <section className="pd-section">
            <h2 className="pd-section-title">
              Today&apos;s Plan — Week {assignment?.current_week}, Day{' '}
              {assignment?.current_day}
            </h2>
            {currentDayPlan ? (
              <div className="pd-exercises-table-wrap">
                <table className="pd-exercises-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Exercise</th>
                      <th>Sets</th>
                      <th>Reps</th>
                      <th>Weight (lbs)</th>
                      <th>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentDayPlan.exercises.map((ex, i) => (
                      <tr key={i}>
                        <td className="pd-ex-order">{i + 1}</td>
                        <td className="pd-ex-name">{ex.exercise_name}</td>
                        <td className="pd-ex-center">{ex.sets}</td>
                        <td className="pd-ex-center">{ex.reps}</td>
                        <td className="pd-ex-center">
                          {ex.weight_lbs != null ? ex.weight_lbs : '—'}
                          {ex.percentage_1rm != null && (
                            <span className="pd-pct-tag">{ex.percentage_1rm}%</span>
                          )}
                        </td>
                        <td className="pd-ex-notes">{ex.notes || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="pd-muted">No exercise data for this day.</p>
            )}
            <button
              className="btn-primary pd-log-inline-btn"
              onClick={() => openLogModal()}
            >
              Log This Workout
            </button>
          </section>

          {/* ── Workout history ── */}
          <section className="pd-section">
            <h2 className="pd-section-title">Workout History</h2>
            {workouts.length === 0 ? (
              <div className="pd-empty">
                <div className="pd-empty-icon">🏋️</div>
                <p>No workouts logged yet. Hit &ldquo;Log Workout&rdquo; to get started.</p>
              </div>
            ) : (
              <div className="pd-history-list">
                {workouts.map((w) => (
                  <div key={w.id} className={`pd-history-item pd-status-${w.status}`}>
                    <div className="pd-history-left">
                      <span className={`pd-status-badge pd-badge-${w.status}`}>
                        {w.status}
                      </span>
                      <span className="pd-history-date">
                        {new Date(w.workout_date).toLocaleDateString(undefined, {
                          weekday: 'short',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </span>
                      {w.duration_minutes && (
                        <span className="pd-history-duration">
                          {w.duration_minutes} min
                        </span>
                      )}
                    </div>
                    <div className="pd-history-right">
                      {w.notes && <span className="pd-history-notes">{w.notes}</span>}
                      <button
                        className="pd-edit-btn"
                        onClick={() => openLogModal(w)}
                        title="Edit"
                      >
                        Edit
                      </button>
                      <button
                        className="pd-delete-btn"
                        onClick={() => handleDelete(w.id)}
                        disabled={deletingId === w.id}
                        title="Delete"
                      >
                        {deletingId === w.id ? '…' : 'Delete'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}

      {/* ── Log / Edit Workout Modal ── */}
      {showLogModal && (
        <div className="modal-overlay" onClick={() => setShowLogModal(false)}>
          <div
            className="modal-content pd-log-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h2>{editingWorkout ? 'Edit Workout' : 'Log Workout'}</h2>
              <button className="modal-close" onClick={() => setShowLogModal(false)}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              {logError && <div className="edit-error-banner">{logError}</div>}

              <div className="form-group">
                <label>Date</label>
                <input
                  type="date"
                  value={logForm.workout_date}
                  onChange={(e) =>
                    setLogForm((f) => ({ ...f, workout_date: e.target.value }))
                  }
                />
              </div>

              <div className="form-group">
                <label>Status</label>
                <div className="pd-status-toggle">
                  <button
                    className={`pd-toggle-btn ${logForm.status === 'completed' ? 'active' : ''}`}
                    onClick={() => setLogForm((f) => ({ ...f, status: 'completed' }))}
                    type="button"
                  >
                    Completed
                  </button>
                  <button
                    className={`pd-toggle-btn ${logForm.status === 'skipped' ? 'active' : ''}`}
                    onClick={() => setLogForm((f) => ({ ...f, status: 'skipped' }))}
                    type="button"
                  >
                    Skipped
                  </button>
                </div>
              </div>

              {logForm.status === 'completed' && (
                <div className="form-group">
                  <label>Duration (minutes)</label>
                  <input
                    type="number"
                    min="1"
                    max="300"
                    placeholder="e.g. 60"
                    value={logForm.duration_minutes}
                    onChange={(e) =>
                      setLogForm((f) => ({ ...f, duration_minutes: e.target.value }))
                    }
                  />
                </div>
              )}

              <div className="form-group">
                <label>Notes</label>
                <textarea
                  rows={3}
                  placeholder="How did the workout go? Any modifications?"
                  value={logForm.notes}
                  onChange={(e) =>
                    setLogForm((f) => ({ ...f, notes: e.target.value }))
                  }
                />
              </div>

              {/* Show today's exercises as a reference inside the modal */}
              {currentDayPlan && logForm.status === 'completed' && (
                <div className="pd-modal-exercises">
                  <p className="pd-modal-exercises-label">
                    Planned exercises for Week {assignment?.current_week}, Day{' '}
                    {assignment?.current_day}:
                  </p>
                  <ul className="pd-modal-exercise-list">
                    {currentDayPlan.exercises.map((ex, i) => (
                      <li key={i}>
                        <strong>{ex.exercise_name}</strong> — {ex.sets}×{ex.reps}
                        {ex.weight_lbs != null && ` @ ${ex.weight_lbs} lbs`}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="modal-footer">
                <button
                  className="btn-secondary"
                  onClick={() => setShowLogModal(false)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  className="btn-primary"
                  onClick={handleLogSubmit}
                  disabled={submitting}
                >
                  {submitting
                    ? 'Saving…'
                    : editingWorkout
                    ? 'Save Changes'
                    : 'Log Workout'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
