import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getMyGeneratedPlan, updateMyGeneratedPlan, startSavedPlan } from '../services/generatedPlans';
import type { SavedPlanDetail, GeneratedPlan } from '../types/engine';
import GeneratedPlanView from '../components/GeneratedPlanView';
import './GeneratedPlanDetail.css';

function todayISO() {
  return new Date().toISOString().split('T')[0];
}

export default function GeneratedPlanDetail() {
  const { planId } = useParams<{ planId: string }>();
  const navigate = useNavigate();

  const [detail, setDetail] = useState<SavedPlanDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  const [startDate, setStartDate] = useState(todayISO());
  const [assignmentName, setAssignmentName] = useState('');
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  useEffect(() => {
    if (!planId) return;
    setLoading(true);
    setError(null);
    getMyGeneratedPlan(planId)
      .then(setDetail)
      .catch(() => setError('Plan not found'))
      .finally(() => setLoading(false));
  }, [planId]);

  async function handlePlanUpdated(updatedPlan: GeneratedPlan) {
    if (!detail || !planId) return;
    setDetail(prev => prev ? { ...prev, plan_data: updatedPlan } : prev);
    setSaving(true);
    setSaveMsg(null);
    try {
      await updateMyGeneratedPlan(planId, { plan_data: updatedPlan });
      setSaveMsg('Changes saved');
      setTimeout(() => setSaveMsg(null), 3000);
    } catch {
      setSaveMsg('Failed to save changes');
    } finally {
      setSaving(false);
    }
  }

  async function handleStart() {
    if (!planId) return;
    setStarting(true);
    setStartError(null);
    try {
      const res = await startSavedPlan(planId, {
        start_date: startDate,
        assignment_name: assignmentName || undefined,
      });
      navigate(`/my-programs/${res.assignment_id}`);
    } catch (err) {
      setStartError(err instanceof Error ? err.message : 'Failed to start program');
    } finally {
      setStarting(false);
    }
  }

  if (loading) return <div className="gpd-page"><p className="gpd-loading">Loading…</p></div>;
  if (error || !detail) return (
    <div className="gpd-page">
      <p className="gpd-error">{error ?? 'Plan not found'}</p>
      <button className="gpd-back-btn" onClick={() => navigate('/my-programs')}>← My Programs</button>
    </div>
  );

  return (
    <div className="gpd-page">
      <div className="gpd-header">
        <button className="gpd-back-btn" onClick={() => navigate('/my-programs')}>← My Programs</button>
        <div className="gpd-title">
          <h1>{detail.name}</h1>
          {detail.notes && <p className="gpd-notes">{detail.notes}</p>}
          <div className="gpd-meta">
            <span className="gpd-program-id">{detail.engine_program_id}</span>
            <span className="gpd-date">Created {new Date(detail.created_at).toLocaleDateString()}</span>
          </div>
        </div>
        <div className="gpd-status">
          {saving && <span className="gpd-saving">Saving…</span>}
          {saveMsg && <span className={`gpd-save-msg ${saveMsg.includes('Failed') ? 'error' : 'ok'}`}>{saveMsg}</span>}
        </div>
      </div>

      <div className="gpd-start-form">
        <h2>Start This Program</h2>
        <p className="gpd-start-desc">
          Review the plan below, then choose a start date to begin tracking your progress.
        </p>
        <div className="gpd-start-fields">
          <label className="gpd-label">
            Start date
            <input
              type="date"
              className="gpd-input"
              value={startDate}
              onChange={e => setStartDate(e.target.value)}
            />
          </label>
          <label className="gpd-label">
            Program name <span className="gpd-optional">(optional)</span>
            <input
              type="text"
              className="gpd-input"
              placeholder={detail.name}
              value={assignmentName}
              onChange={e => setAssignmentName(e.target.value)}
            />
          </label>
        </div>
        {startError && <p className="gpd-error">{startError}</p>}
        <button
          className="gpd-start-btn"
          onClick={handleStart}
          disabled={starting}
        >
          {starting ? 'Starting…' : 'Start Program'}
        </button>
      </div>

      <GeneratedPlanView
        plan={detail.plan_data}
        editable={true}
        onPlanUpdated={handlePlanUpdated}
        assignment={null}
      />
    </div>
  );
}
