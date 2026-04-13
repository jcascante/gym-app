import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listMyGeneratedPlans, deleteMyGeneratedPlan } from '../services/generatedPlans';
import type { SavedPlanSummary } from '../types/engine';
import './MyGeneratedPlans.css';

export default function MyGeneratedPlans() {
  const navigate = useNavigate();
  const [plans, setPlans] = useState<SavedPlanSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    listMyGeneratedPlans()
      .then(setPlans)
      .catch(() => setError('Failed to load plans'))
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(id: string) {
    if (!confirm('Delete this plan?')) return;
    setDeleting(id);
    try {
      await deleteMyGeneratedPlan(id);
      setPlans(prev => prev.filter(p => p.id !== id));
    } catch {
      setError('Failed to delete plan');
    } finally {
      setDeleting(null);
    }
  }

  return (
    <div className="mgp-page">
      <div className="mgp-header">
        <div>
          <h1>My Plans</h1>
          <p>Plans you've built but haven't started yet. Start one when you're ready.</p>
        </div>
        <button className="mgp-build-btn" onClick={() => navigate('/build-program')}>
          + Build new plan
        </button>
      </div>

      {error && <div className="mgp-error">{error}</div>}

      {loading ? (
        <p className="mgp-loading">Loading…</p>
      ) : plans.length === 0 ? (
        <div className="mgp-empty">
          <p>No unstarted plans. Build a new one or check <button className="mgp-link-btn" onClick={() => navigate('/my-programs')}>My Programs</button> for active programs.</p>
          <button className="mgp-build-btn" onClick={() => navigate('/build-program')}>
            Build a plan
          </button>
        </div>
      ) : (
        <div className="mgp-list">
          {plans.map(plan => (
            <div key={plan.id} className="mgp-card" onClick={() => navigate(`/my-generated-plans/${plan.id}`)}>
              <div className="mgp-card-body">
                <h3 style={{ margin: '0 0 0.25rem' }}>{plan.name}</h3>
                {plan.notes && <p className="mgp-notes">{plan.notes}</p>}
                <div className="mgp-meta">
                  <span className="mgp-program-id">{plan.engine_program_id}</span>
                  <span className="mgp-date">{new Date(plan.created_at).toLocaleDateString()}</span>
                </div>
              </div>
              <button
                className="mgp-delete-btn"
                disabled={deleting === plan.id}
                onClick={e => { e.stopPropagation(); handleDelete(plan.id); }}
              >
                {deleting === plan.id ? '…' : 'Delete'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
