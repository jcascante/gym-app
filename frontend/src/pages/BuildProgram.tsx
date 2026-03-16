import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listProgramDefinitions, getProgramDefinition, generatePlan } from '../services/engineProxy';
import { savePlan } from '../services/generatedPlans';
import type { EngineProgramSummary, EngineProgramDefinition, GeneratedPlan, ParameterField } from '../types/engine';
import DynamicParamForm from '../components/DynamicParamForm';
import GeneratedPlanView from '../components/GeneratedPlanView';
import './BuildProgram.css';

type Step = 'select' | 'configure' | 'generating' | 'review' | 'saving' | 'done';

// Convert { 'athlete.level': 'x', 'athlete.e1rm.squat': 100 }
// into nested { athlete: { level: 'x', e1rm: { squat: 100 } } }
function buildNested(flat: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [dotPath, value] of Object.entries(flat)) {
    const keys = dotPath.split('.');
    let cur: Record<string, unknown> = result;
    for (let i = 0; i < keys.length - 1; i++) {
      if (!cur[keys[i]] || typeof cur[keys[i]] !== 'object') {
        cur[keys[i]] = {};
      }
      cur = cur[keys[i]] as Record<string, unknown>;
    }
    cur[keys[keys.length - 1]] = value;
  }
  return result;
}

// Mirror of DynamicParamForm's applyDefault — resolves a field's default value.
function resolveDefault(field: ParameterField): unknown {
  const d = field.default_expr;
  if (d == null) {
    if (field.type === 'string_array' || field.type === 'number_array') return [];
    if (field.type === 'boolean') return false;
    return undefined; // no default — omit from payload
  }
  if (d === '[]') return [];
  if (d === 'true') return true;
  if (d === 'false') return false;
  const n = Number(d);
  if (!isNaN(n) && d !== '') return n;
  return d.replace(/^['"]|['"]$/g, '');
}

// Build the effective flat values map: user-provided values take precedence,
// fields the user never touched fall back to their default_expr.
// Fields with no default and no user value are omitted (engine will validate).
function effectiveValues(
  fields: ParameterField[],
  userValues: Record<string, unknown>,
): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const field of fields) {
    if (field.key in userValues) {
      result[field.key] = userValues[field.key];
    } else {
      const def = resolveDefault(field);
      if (def !== undefined) result[field.key] = def;
    }
  }
  return result;
}

export default function BuildProgram() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('select');
  const [programs, setPrograms] = useState<EngineProgramSummary[]>([]);
  const [loadingPrograms, setLoadingPrograms] = useState(true);
  const [engineError, setEngineError] = useState<string | null>(null);

  const [selected, setSelected] = useState<EngineProgramSummary | null>(null);
  const [definition, setDefinition] = useState<EngineProgramDefinition | null>(null);
  const [formValues, setFormValues] = useState<Record<string, unknown>>({});
  const [weeks, setWeeks] = useState(4);
  const [daysPerWeek, setDaysPerWeek] = useState(4);

  const [generatedPlan, setGeneratedPlan] = useState<GeneratedPlan | null>(null);
  const [saveName, setSaveName] = useState('');
  const [saveNotes, setSaveNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listProgramDefinitions()
      .then(setPrograms)
      .catch(() => setEngineError('Could not connect to the training engine. Is it running?'))
      .finally(() => setLoadingPrograms(false));
  }, []);

  async function handleSelectProgram(prog: EngineProgramSummary) {
    setError(null);
    try {
      const def = await getProgramDefinition(prog.program_id);
      setSelected(prog);
      setDefinition(def);
      setWeeks(def.template.weeks.min);
      setDaysPerWeek(def.template.days_per_week.min);
      setFormValues({});
      setStep('configure');
    } catch {
      setError('Failed to load program details');
    }
  }

  async function handleGenerate() {
    if (!selected || !definition) return;
    setStep('generating');
    setError(null);
    // Merge user-provided values with field defaults so the engine always
    // receives every expected key (e.g. rules.main_method) even if untouched.
    const merged = effectiveValues(definition.parameter_spec.fields, formValues);
    const nested = buildNested(merged);
    const payload = {
      program_id: selected.program_id,
      program_version: selected.version,
      weeks,
      days_per_week: daysPerWeek,
      ...nested,
      seed: Date.now(),
    };
    try {
      const plan = await generatePlan(payload);
      setGeneratedPlan(plan);
      setSaveName(`${selected.name ?? selected.program_id} — ${new Date().toLocaleDateString()}`);
      setStep('review');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Generation failed');
      setStep('configure');
    }
  }

  async function handleSave() {
    if (!generatedPlan || !selected) return;
    if (!saveName.trim()) {
      setError('Please enter a name for your plan');
      return;
    }
    setStep('saving');
    setError(null);
    try {
      await savePlan({
        name: saveName.trim(),
        notes: saveNotes.trim() || undefined,
        engine_program_id: selected.program_id,
        engine_program_version: selected.version,
        inputs_echo: generatedPlan.inputs_echo,
        plan_data: generatedPlan,
      });
      setStep('done');
    } catch {
      setError('Failed to save plan');
      setStep('review');
    }
  }

  // ── SELECT STEP ──────────────────────────────────────────
  if (step === 'select') {
    return (
      <div className="bp-page">
        <div className="bp-header">
          <h1>Build My Program</h1>
          <p>Choose a training program template to get started.</p>
        </div>
        {engineError && <div className="bp-error">{engineError}</div>}
        {loadingPrograms ? (
          <p className="bp-loading">Loading programs…</p>
        ) : (
          <div className="bp-program-grid">
            {programs.map(p => (
              <button key={p.program_id} className="bp-program-card" onClick={() => handleSelectProgram(p)}>
                <h3>{p.name ?? p.program_id}</h3>
                <p>{p.description ?? ''}</p>
                <span className="bp-program-id">{p.program_id}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ── CONFIGURE STEP ───────────────────────────────────────
  if (step === 'configure' && definition) {
    const wMin = definition.template.weeks.min;
    const wMax = definition.template.weeks.max;
    const dMin = definition.template.days_per_week.min;
    const dMax = definition.template.days_per_week.max;

    return (
      <div className="bp-page">
        <div className="bp-header">
          <button className="bp-back" onClick={() => setStep('select')}>← Back</button>
          <h1>{selected?.name ?? selected?.program_id}</h1>
          <p>Fill in your details to generate a personalised plan.</p>
        </div>
        {error && <div className="bp-error">{error}</div>}

        <div className="bp-configure-layout">
          <div className="bp-schedule-section">
            <h3>Schedule</h3>
            <div className="bp-slider-field">
              <label>Weeks: <strong>{weeks}</strong></label>
              <input type="range" min={wMin} max={wMax} value={weeks} onChange={e => setWeeks(Number(e.target.value))} />
              <span className="bp-range-hint">{wMin}–{wMax}</span>
            </div>
            {dMin !== dMax && (
              <div className="bp-slider-field">
                <label>Days per week: <strong>{daysPerWeek}</strong></label>
                <input type="range" min={dMin} max={dMax} value={daysPerWeek} onChange={e => setDaysPerWeek(Number(e.target.value))} />
                <span className="bp-range-hint">{dMin}–{dMax}</span>
              </div>
            )}
          </div>

          <div className="bp-params-section">
            <h3>Program Parameters</h3>
            <DynamicParamForm
              fields={definition.parameter_spec.fields}
              values={formValues}
              onChange={(key, val) => setFormValues(prev => ({ ...prev, [key]: val }))}
            />
          </div>
        </div>

        <div className="bp-actions">
          <button className="bp-btn-primary" onClick={handleGenerate}>
            Generate My Plan →
          </button>
        </div>
      </div>
    );
  }

  // ── GENERATING ───────────────────────────────────────────
  if (step === 'generating') {
    return (
      <div className="bp-page bp-center">
        <div className="bp-spinner" />
        <p>Generating your personalised training plan…</p>
      </div>
    );
  }

  // ── REVIEW STEP ──────────────────────────────────────────
  if (step === 'review' && generatedPlan) {
    return (
      <div className="bp-page">
        <div className="bp-header">
          <h1>Your Training Plan</h1>
          <p>Review your plan. Click <strong>Swap</strong> on any exercise to replace it.</p>
        </div>
        {error && <div className="bp-error">{error}</div>}

        <GeneratedPlanView
          plan={generatedPlan}
          editable
          onPlanUpdated={setGeneratedPlan}
        />

        <div className="bp-save-section">
          <h3>Save this plan</h3>
          <input
            className="bp-save-input"
            type="text"
            placeholder="Plan name *"
            value={saveName}
            onChange={e => setSaveName(e.target.value)}
          />
          <textarea
            className="bp-save-input"
            placeholder="Notes (optional)"
            rows={2}
            value={saveNotes}
            onChange={e => setSaveNotes(e.target.value)}
          />
          <div className="bp-actions">
            <button className="bp-btn-secondary" onClick={() => setStep('configure')}>
              ← Reconfigure
            </button>
            <button className="bp-btn-primary" onClick={handleSave}>
              Save Plan
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── SAVING ───────────────────────────────────────────────
  if (step === 'saving') {
    return (
      <div className="bp-page bp-center">
        <div className="bp-spinner" />
        <p>Saving your plan…</p>
      </div>
    );
  }

  // ── DONE ─────────────────────────────────────────────────
  if (step === 'done') {
    return (
      <div className="bp-page bp-center">
        <div className="bp-success-icon">✓</div>
        <h2>Plan saved!</h2>
        <p>Your training plan is ready.</p>
        <div className="bp-actions">
          <button className="bp-btn-secondary" onClick={() => navigate('/build-program')}>
            Build another
          </button>
          <button className="bp-btn-primary" onClick={() => navigate('/my-generated-plans')}>
            View my plans →
          </button>
        </div>
      </div>
    );
  }

  return null;
}
