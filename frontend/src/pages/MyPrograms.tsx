import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMyPrograms } from '../services/programAssignments';
import { listMyGeneratedPlans } from '../services/generatedPlans';
import type { ProgramAssignmentSummary } from '../services/programAssignments';
import type { SavedPlanSummary } from '../types/engine';
import './Programs.css';

function progressColor(pct: number): string {
  if (pct >= 70) return '#2e7d32';
  if (pct >= 40) return '#f57c00';
  return '#c62828';
}

export default function MyPrograms() {
  const [assignments, setAssignments] = useState<ProgramAssignmentSummary[]>([]);
  const [drafts, setDrafts] = useState<SavedPlanSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const [programsRes, draftsRes] = await Promise.all([
          getMyPrograms(),
          listMyGeneratedPlans(true),
        ]);
        setAssignments(programsRes.programs || []);
        setDrafts(draftsRes);
      } catch {
        setError('Failed to load programs');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const isEmpty = assignments.length === 0 && drafts.length === 0;

  return (
    <div className="programs-page">
      <div className="programs-header">
        <h1>My Programs</h1>
        <p>Your active programs and saved drafts</p>
        <button
          className="btn-primary"
          style={{ marginTop: '0.75rem' }}
          onClick={() => navigate('/build-program')}
        >
          + Build a program
        </button>
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {loading ? (
        <p>Loading...</p>
      ) : isEmpty ? (
        <div style={{ textAlign: 'center', padding: '2rem 0', color: '#666' }}>
          <p>You don't have any programs yet.</p>
          <button className="btn-primary" onClick={() => navigate('/build-program')}>
            Build your first program
          </button>
        </div>
      ) : (
        <div className="programs-grid">
          {/* Draft plans */}
          {drafts.map((plan) => (
            <div
              key={`draft-${plan.id}`}
              className="program-card"
              role="button"
              tabIndex={0}
              onClick={() => navigate(`/my-generated-plans/${plan.id}`)}
              onKeyDown={(e) => e.key === 'Enter' && navigate(`/my-generated-plans/${plan.id}`)}
              style={{ cursor: 'pointer' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                <h3 style={{ margin: 0 }}>{plan.name}</h3>
                <span style={{
                  fontSize: '0.7rem', fontWeight: 600, padding: '0.15rem 0.5rem',
                  borderRadius: '10px', background: '#fff3e0', color: '#e65100',
                  textTransform: 'uppercase', letterSpacing: '0.04em', whiteSpace: 'nowrap',
                }}>Draft</span>
              </div>
              {plan.notes && (
                <p style={{ color: '#666', margin: '0 0 0.5rem', fontSize: '0.875rem' }}>{plan.notes}</p>
              )}
              <div className="program-meta" style={{ marginBottom: '0.75rem' }}>
                <span>{plan.engine_program_id}</span>
                <span>Built {new Date(plan.created_at).toLocaleDateString()}</span>
              </div>
              <button
                className="btn-primary"
                style={{ width: '100%' }}
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/my-generated-plans/${plan.id}`);
                }}
              >
                Review &amp; Start
              </button>
            </div>
          ))}

          {/* Active assignments */}
          {assignments.map((p) => {
            const pct = Math.round(p.progress_percentage);
            const color = progressColor(pct);
            return (
              <div
                key={`assign-${p.assignment_id}`}
                className="program-card"
                role="button"
                tabIndex={0}
                onClick={() => navigate(`/my-programs/${p.assignment_id}`)}
                onKeyDown={(e) => e.key === 'Enter' && navigate(`/my-programs/${p.assignment_id}`)}
                style={{ cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.25rem' }}>
                  <h3 style={{ margin: 0 }}>{p.assignment_name || p.program_name}</h3>
                  <span style={{
                    fontSize: '0.7rem', fontWeight: 600, padding: '0.15rem 0.5rem',
                    borderRadius: '10px', background: p.status === 'completed' ? '#e8f5e9' : '#e3f2fd',
                    color: p.status === 'completed' ? '#2e7d32' : '#1565c0',
                    textTransform: 'capitalize', letterSpacing: '0.04em', whiteSpace: 'nowrap',
                  }}>{p.status}</span>
                </div>

                <div style={{ marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#666', marginBottom: '0.25rem' }}>
                    <span>Week {p.current_week} · Day {p.current_day}</span>
                    <span style={{ color }}>{pct}%</span>
                  </div>
                  <div style={{ height: '6px', background: '#e0e0e0', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: '3px', transition: 'width 0.3s' }} />
                  </div>
                </div>

                <div className="program-meta">
                  <span>{p.duration_weeks}w</span>
                  <span>{p.days_per_week}d/w</span>
                </div>

                {p.status !== 'completed' && p.status !== 'cancelled' && (
                  <button
                    className="btn-primary"
                    style={{ marginTop: '0.75rem', width: '100%' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/log/${p.assignment_id}`, {
                        state: { returnTo: `/my-programs/${p.assignment_id}` },
                      });
                    }}
                  >
                    Log Today's Workout
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
