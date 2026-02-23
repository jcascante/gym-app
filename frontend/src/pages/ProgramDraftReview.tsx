import { useState, useEffect } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import {
  getProgramDetail,
  deleteProgram,
  publishProgram,
  updateProgramExercise,
  type ProgramDetail,
  type ExerciseDetail,
} from '../services/programs';
import { ApiError } from '../services/api';
import './ProgramDraftReview.css';
import './ProgramDetails.css'; // reuse pd- classes

export default function ProgramDraftReview() {
  const { programId } = useParams<{ programId: string }>();
  const [searchParams] = useSearchParams();
  const clientId = searchParams.get('clientId');
  const navigate = useNavigate();

  const [program, setProgram] = useState<ProgramDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeWeek, setActiveWeek] = useState(1);

  // Inline edit state: keyed by exercise ID
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<{ sets: number; reps: number; weight_lbs: number; notes: string }>({
    sets: 0, reps: 0, weight_lbs: 0, notes: '',
  });
  const [saving, setSaving] = useState(false);

  // Action state
  const [publishing, setPublishing] = useState(false);
  const [discarding, setDiscarding] = useState(false);

  useEffect(() => {
    if (!programId) return;
    setLoading(true);
    getProgramDetail(programId)
      .then(data => {
        setProgram(data);
        setActiveWeek(data.weeks[0]?.week_number ?? 1);
      })
      .catch(err => {
        if (err instanceof ApiError) setError(err.message);
        else setError('Failed to load program.');
      })
      .finally(() => setLoading(false));
  }, [programId]);

  const startEdit = (ex: ExerciseDetail) => {
    if (!ex.id) return;
    setEditingId(ex.id);
    setEditForm({
      sets: ex.sets,
      reps: ex.reps,
      weight_lbs: ex.weight_lbs ?? 0,
      notes: ex.notes ?? '',
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
  };

  const saveEdit = async (ex: ExerciseDetail) => {
    if (!programId || !ex.id) return;
    setSaving(true);
    try {
      const updated = await updateProgramExercise(programId, ex.id, {
        sets: editForm.sets,
        reps: editForm.reps,
        reps_target: editForm.reps,
        weight_lbs: editForm.weight_lbs || undefined,
        load_value: editForm.weight_lbs || undefined,
        notes: editForm.notes,
      });

      // Update local program state
      setProgram(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          weeks: prev.weeks.map(w => ({
            ...w,
            days: w.days.map(d => ({
              ...d,
              exercises: d.exercises.map(e =>
                e.id === ex.id
                  ? {
                      ...e,
                      sets: updated.sets,
                      reps: updated.reps ?? e.reps,
                      weight_lbs: updated.weight_lbs,
                      notes: updated.notes ?? '',
                    }
                  : e
              ),
            })),
          })),
        };
      });
      setEditingId(null);
    } catch (err) {
      alert(`Failed to save: ${err instanceof ApiError ? err.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  };

  const handleDiscard = async () => {
    if (!programId) return;
    if (!confirm('Discard this draft? The program and its assignment will be permanently removed.')) return;
    setDiscarding(true);
    try {
      await deleteProgram(programId);
      navigate('/programs');
    } catch (err) {
      alert(`Failed to discard: ${err instanceof ApiError ? err.message : 'Unknown error'}`);
      setDiscarding(false);
    }
  };

  const handleSaveClose = () => {
    navigate(clientId ? `/clients/${clientId}` : '/programs');
  };

  const handlePublish = async () => {
    if (!programId) return;
    if (!confirm('Publish this program? The client will be able to see and track it.')) return;
    setPublishing(true);
    try {
      await publishProgram(programId);
      navigate(clientId ? `/clients/${clientId}` : '/programs');
    } catch (err) {
      alert(`Failed to publish: ${err instanceof ApiError ? err.message : 'Unknown error'}`);
      setPublishing(false);
    }
  };

  if (loading) {
    return (
      <div className="pdr-page">
        <div className="pdr-loading">
          <div className="spinner" />
          <span>Loading draft program...</span>
        </div>
      </div>
    );
  }

  if (error || !program) {
    return (
      <div className="pdr-page">
        <div className="pdr-error">{error || 'Program not found.'}</div>
      </div>
    );
  }

  const activeWeekData = program.weeks.find(w => w.week_number === activeWeek);

  return (
    <div className="pdr-page">
      {/* Header */}
      <div className="pdr-header">
        <button className="pdr-back-btn" onClick={() => navigate(clientId ? `/clients/${clientId}` : '/programs')}>
          ← Back
        </button>
        <div className="pdr-header-info">
          <h1>
            {program.name}
            <span className="pdr-draft-badge">Draft</span>
          </h1>
        </div>
      </div>

      {/* Stats bar */}
      <div className="pd-stats-bar">
        <div className="pd-stat">
          <span className="pd-stat-value">{program.duration_weeks}</span>
          <span className="pd-stat-label">Weeks</span>
        </div>
        <div className="pd-stat">
          <span className="pd-stat-value">{program.days_per_week}</span>
          <span className="pd-stat-label">Days / wk</span>
        </div>
        <div className="pd-stat">
          <span className="pd-stat-value">{program.weeks.reduce((acc, w) => acc + w.days.reduce((a, d) => a + d.exercises.length, 0), 0)}</span>
          <span className="pd-stat-label">Exercises</span>
        </div>
      </div>

      {/* Week tabs */}
      <div className="pdr-week-tabs">
        {program.weeks.map(w => (
          <button
            key={w.week_number}
            className={`pdr-week-tab${w.week_number === activeWeek ? ' active' : ''}`}
            onClick={() => setActiveWeek(w.week_number)}
          >
            Week {w.week_number}
          </button>
        ))}
      </div>

      {/* Week content */}
      {activeWeekData && (
        <>
          {activeWeekData.days.map(day => (
            <div key={day.day_number} className="pdr-day-section">
              <p className="pdr-day-title">Day {day.day_number} — {day.name}</p>

              <div className="pd-exercises-table-wrap">
                <table className="pd-exercises-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Exercise</th>
                      <th className="pd-ex-center">Sets</th>
                      <th className="pd-ex-center">Reps</th>
                      <th className="pd-ex-center">Weight (lbs)</th>
                      <th>Notes</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {day.exercises.map((ex, idx) => (
                      <tr key={ex.id ?? idx}>
                        {editingId === ex.id ? (
                          /* Inline edit row */
                          <>
                            <td className="pd-ex-order">{idx + 1}</td>
                            <td className="pd-ex-name">{ex.exercise_name}</td>
                            <td className="pd-ex-center">
                              <input
                                className="pdr-edit-input"
                                type="number"
                                min={1}
                                value={editForm.sets}
                                onChange={e => setEditForm(f => ({ ...f, sets: parseInt(e.target.value) || 1 }))}
                              />
                            </td>
                            <td className="pd-ex-center">
                              <input
                                className="pdr-edit-input"
                                type="number"
                                min={1}
                                value={editForm.reps}
                                onChange={e => setEditForm(f => ({ ...f, reps: parseInt(e.target.value) || 1 }))}
                              />
                            </td>
                            <td className="pd-ex-center">
                              <input
                                className="pdr-edit-input"
                                type="number"
                                min={0}
                                step={5}
                                value={editForm.weight_lbs || ''}
                                onChange={e => setEditForm(f => ({ ...f, weight_lbs: parseFloat(e.target.value) || 0 }))}
                              />
                            </td>
                            <td colSpan={2}>
                              <div className="pdr-edit-row">
                                <input
                                  type="text"
                                  placeholder="Notes..."
                                  value={editForm.notes}
                                  onChange={e => setEditForm(f => ({ ...f, notes: e.target.value }))}
                                  style={{ flex: 1, padding: '0.35rem 0.5rem', border: '1px solid #1976d2', borderRadius: '5px', fontSize: '0.88rem' }}
                                />
                                <button
                                  className="pdr-save-btn"
                                  onClick={() => saveEdit(ex)}
                                  disabled={saving}
                                >
                                  {saving ? '...' : 'Save'}
                                </button>
                                <button className="pdr-cancel-btn" onClick={cancelEdit} disabled={saving}>
                                  Cancel
                                </button>
                              </div>
                            </td>
                          </>
                        ) : (
                          /* Normal display row */
                          <>
                            <td className="pd-ex-order">{idx + 1}</td>
                            <td className="pd-ex-name">{ex.exercise_name}</td>
                            <td className="pd-ex-center">{ex.sets}</td>
                            <td className="pd-ex-center">{ex.reps}</td>
                            <td className="pd-ex-center">
                              {ex.weight_lbs != null ? ex.weight_lbs : <span className="pd-muted">—</span>}
                              {ex.percentage_1rm != null && (
                                <span className="pd-pct-tag">{ex.percentage_1rm}%</span>
                              )}
                            </td>
                            <td className="pd-ex-notes">{ex.notes || ''}</td>
                            <td>
                              {ex.id && (
                                <button
                                  className="pd-edit-btn"
                                  onClick={() => startEdit(ex)}
                                  title="Edit exercise"
                                >
                                  Edit
                                </button>
                              )}
                            </td>
                          </>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </>
      )}

      {/* Action bar */}
      <div className="pdr-action-bar">
        <button
          className="pdr-discard-btn"
          onClick={handleDiscard}
          disabled={discarding || publishing}
        >
          {discarding ? 'Discarding...' : 'Discard Draft'}
        </button>
        <button
          className="pdr-cancel-btn"
          style={{ borderRadius: '7px', padding: '0.55rem 1.1rem', fontSize: '0.9rem' }}
          onClick={handleSaveClose}
          disabled={discarding || publishing}
        >
          Save &amp; Close
        </button>
        <button
          className="pdr-publish-btn"
          onClick={handlePublish}
          disabled={publishing || discarding}
        >
          {publishing ? 'Publishing...' : 'Publish Program'}
        </button>
      </div>
    </div>
  );
}
