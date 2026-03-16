import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getMyGeneratedPlan, updateMyGeneratedPlan } from '../services/generatedPlans';
import type { SavedPlanDetail, GeneratedPlan } from '../types/engine';
import GeneratedPlanView from '../components/GeneratedPlanView';
import './GeneratedPlanDetail.css';

export default function GeneratedPlanDetail() {
  const { planId } = useParams<{ planId: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<SavedPlanDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!planId) return;
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

  if (loading) return <div className="gpd-page"><p className="gpd-loading">Loading…</p></div>;
  if (error || !detail) return (
    <div className="gpd-page">
      <p className="gpd-error">{error ?? 'Plan not found'}</p>
      <button className="gpd-back-btn" onClick={() => navigate('/my-generated-plans')}>← Back</button>
    </div>
  );

  return (
    <div className="gpd-page">
      <div className="gpd-header">
        <button className="gpd-back-btn" onClick={() => navigate('/my-generated-plans')}>← My Plans</button>
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

      <GeneratedPlanView
        plan={detail.plan_data}
        editable
        onPlanUpdated={handlePlanUpdated}
      />
    </div>
  );
}
