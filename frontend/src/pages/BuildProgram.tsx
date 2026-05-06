import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listProgramDefinitions, getProgramDefinition, generatePlan } from '../services/engineProxy';
import { ApiError } from '../services/api';
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
  const [highlighted, setHighlighted] = useState<EngineProgramSummary | null>(null);
  const [definition, setDefinition] = useState<EngineProgramDefinition | null>(null);
  const [formValues, setFormValues] = useState<Record<string, unknown>>({});
  const [weeks, setWeeks] = useState(4);
  const [daysPerWeek, setDaysPerWeek] = useState(4);

  const [search, setSearch] = useState('');
  const [activeFilters, setActiveFilters] = useState<Set<string>>(new Set());

  const [generatedPlan, setGeneratedPlan] = useState<GeneratedPlan | null>(null);
  const [saveName, setSaveName] = useState('');
  const [saveNotes, setSaveNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listProgramDefinitions()
      .then(setPrograms)
      .catch((err: unknown) => {
        const detail = err instanceof ApiError ? err.message : 'Could not connect to the training engine.';
        setEngineError(detail);
      })
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
    const allFilters = Array.from(
      new Set(programs.flatMap(p => [p.category, ...p.tags].filter(Boolean) as string[]))
    ).sort();

    const filtered = programs.filter(p => {
      const q = search.toLowerCase();
      const matchesSearch =
        !q ||
        (p.name ?? '').toLowerCase().includes(q) ||
        (p.description ?? '').toLowerCase().includes(q) ||
        (p.category ?? '').toLowerCase().includes(q);
      const matchesFilters =
        activeFilters.size === 0 ||
        [...activeFilters].some(
          f => p.category === f || p.tags.includes(f),
        );
      return matchesSearch && matchesFilters;
    });

    const detail = highlighted ?? (filtered.length === 1 ? filtered[0] : null);

    function toggleFilter(f: string) {
      setActiveFilters(prev => {
        const next = new Set(prev);
        if (next.has(f)) { next.delete(f); } else { next.add(f); }
        return next;
      });
    }

    function formatDays(p: EngineProgramSummary) {
      const { min, max } = p.days_per_week;
      return min === max ? `${min} days/week` : `${min}–${max} days/week`;
    }

    return (
      <div className="bp-page bp-select-page">
        <div className="bp-header">
          <h1>Build My Program</h1>
          <p>Choose a training program template to get started.</p>
        </div>

        {engineError && <div className="bp-error">{engineError}</div>}

        {/* Search */}
        <div className="bp-search-bar">
          <span className="bp-search-icon">🔍</span>
          <input
            type="search"
            placeholder="Search programs…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="bp-search-input"
          />
        </div>

        {/* Filter chips */}
        {allFilters.length > 0 && (
          <div className="bp-filter-bar">
            <button
              className={`bp-chip ${activeFilters.size === 0 ? 'bp-chip--active' : ''}`}
              onClick={() => setActiveFilters(new Set())}
            >
              All
            </button>
            {allFilters.map(f => (
              <button
                key={f}
                className={`bp-chip ${activeFilters.has(f) ? 'bp-chip--active' : ''}`}
                onClick={() => toggleFilter(f)}
              >
                {f}
              </button>
            ))}
          </div>
        )}

        {loadingPrograms ? (
          <div className="bp-skeleton-list">
            {[1, 2, 3].map(i => <div key={i} className="bp-skeleton-card" />)}
          </div>
        ) : (
          <div className="bp-master-detail">
            {/* Left: program list */}
            <div className="bp-program-list">
              {filtered.length === 0 && (
                <p className="bp-empty">No programs match your search.</p>
              )}
              {filtered.map(p => (
                <button
                  key={p.program_id}
                  className={`bp-list-card ${detail?.program_id === p.program_id ? 'bp-list-card--active' : ''}`}
                  onClick={() => setHighlighted(p)}
                >
                  <div className="bp-list-card-name">{p.name ?? p.program_id}</div>
                  <div className="bp-list-card-meta">
                    {p.category && <span className="bp-badge bp-badge--category">{p.category}</span>}
                    <span className="bp-badge bp-badge--days">{formatDays(p)}</span>
                  </div>
                </button>
              ))}
            </div>

            {/* Right: detail panel */}
            <div className="bp-detail-panel">
              {!detail ? (
                <div className="bp-detail-empty">
                  <span className="bp-detail-empty-icon">←</span>
                  <p>Select a program to see details</p>
                </div>
              ) : (
                <>
                  <div className="bp-detail-badges">
                    {detail.category && (
                      <span className="bp-badge bp-badge--category">{detail.category}</span>
                    )}
                    {detail.tags.map(t => (
                      <span key={t} className="bp-badge bp-badge--tag">{t}</span>
                    ))}
                  </div>

                  <h2 className="bp-detail-name">{detail.name ?? detail.program_id}</h2>

                  <div className="bp-detail-schedule">
                    <div className="bp-detail-stat">
                      <span className="bp-detail-stat-value">{formatDays(detail)}</span>
                    </div>
                    <div className="bp-detail-stat">
                      <span className="bp-detail-stat-value">
                        {detail.weeks.min === detail.weeks.max
                          ? `${detail.weeks.min} weeks`
                          : `${detail.weeks.min}–${detail.weeks.max} weeks`}
                      </span>
                    </div>
                  </div>

                  <p className="bp-detail-description">{detail.description}</p>

                  <div className="bp-detail-actions">
                    <button
                      className="bp-btn-primary bp-btn-large"
                      onClick={() => handleSelectProgram(detail)}
                    >
                      Build This Program →
                    </button>
                  </div>
                </>
              )}
            </div>
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
