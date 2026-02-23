import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useSearchParams } from 'react-router-dom';
import './ProgramBuilder.css';
import {
  fetchCalculationConstants,
  calculateWeeklyJump,
  calculateRampUp,
  calculate80Percent
} from '../services/programCalculations';
import { apiFetch } from '../services/api';
import { getClientDetail, listMyClients, type ClientDetailResponse, type OneRepMax, type ClientSummary } from '../services/clients';

// ─── Types ──────────────────────────────────────────────────────────────────

interface Movement {
  id: string;
  name: string;
  oneRM: number;
  eightyPercentRM: number;
  maxRepsAt80: number;
  weeklyJumpPercent: number;
  weeklyJumpLbs: number;
  rampUpPercent: number;
  rampUpBaseLbs: number;
  targetWeight: number;
  fromProfile?: boolean;
}

type Step = 'selectClient' | 'clientContext' | 'templateSelect' | 'movements' | 'oneRM' | 'eightyPercentTest' | 'fiveRMTest' | 'program';

// ─── Template catalogue ──────────────────────────────────────────────────────

interface TemplateOption {
  id: string;
  name: string;
  tag: string;
  tagColor: string;
  description: string;
  duration_weeks: number;
  days_per_week: number;
  available: boolean;
  goals: string[];
}

const TEMPLATES: TemplateOption[] = [
  {
    id: 'strength_linear_5x5',
    name: 'Strength Linear 5×5',
    tag: 'Strength',
    tagColor: '#1565c0',
    description: 'Linear progression with barbell compound movements. Builds raw strength through systematic weekly overload.',
    duration_weeks: 8,
    days_per_week: 4,
    available: true,
    goals: ['strength'],
  },
  {
    id: 'hypertrophy_block',
    name: 'Hypertrophy Block (PPL)',
    tag: 'Hypertrophy',
    tagColor: '#6a1b9a',
    description: 'Push / Pull / Legs split with moderate intensity and high volume focused on muscle growth.',
    duration_weeks: 12,
    days_per_week: 6,
    available: false,
    goals: ['hypertrophy'],
  },
  {
    id: 'general_fitness',
    name: 'General Fitness Foundation',
    tag: 'General',
    tagColor: '#2e7d32',
    description: 'Balanced program combining strength, cardio, and mobility for overall fitness improvement.',
    duration_weeks: 8,
    days_per_week: 3,
    available: false,
    goals: ['general_fitness', 'rehabilitation'],
  },
  {
    id: 'athletic_performance',
    name: 'Athletic Performance',
    tag: 'Athletic',
    tagColor: '#b71c1c',
    description: 'Power, speed, and agility training for sport-specific performance enhancement.',
    duration_weeks: 10,
    days_per_week: 4,
    available: false,
    goals: ['athletic_performance'],
  },
  {
    id: 'fat_loss_circuit',
    name: 'Fat Loss Circuit',
    tag: 'Fat Loss',
    tagColor: '#e65100',
    description: 'High-intensity circuit training combining resistance and metabolic conditioning for fat loss.',
    duration_weeks: 8,
    days_per_week: 4,
    available: false,
    goals: ['fat_loss'],
  },
];

const GOAL_LABELS: Record<string, string> = {
  strength: 'Strength',
  hypertrophy: 'Hypertrophy / Muscle Building',
  fat_loss: 'Fat Loss',
  athletic_performance: 'Athletic Performance',
  general_fitness: 'General Fitness',
  rehabilitation: 'Rehabilitation',
};

const EXPERIENCE_LABELS: Record<string, string> = {
  beginner: 'Beginner (0–1 yr)',
  novice: 'Novice (1–2 yrs)',
  intermediate: 'Intermediate (2–5 yrs)',
  advanced: 'Advanced (5–10 yrs)',
  elite: 'Elite (10+ yrs)',
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function ProgramBuilder() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClientId = searchParams.get('clientId');

  // ─── Existing state ────────────────────────────────────────────────────────
  const [selectedClientId, setSelectedClientId] = useState<string | null>(queryClientId);
  const [currentStep, setCurrentStep] = useState<Step>(queryClientId ? 'clientContext' : 'selectClient');
  const [movements, setMovements] = useState<Movement[]>([]);
  const [selectedMovement, setSelectedMovement] = useState<Movement | null>(null);
  const [newMovementName, setNewMovementName] = useState('');
  const [selectedWeek, setSelectedWeek] = useState<number | 'all'>(1);
  const [lastSingleWeek, setLastSingleWeek] = useState<number>(1);
  const [isSaving, setIsSaving] = useState(false);
  const [constantsLoaded, setConstantsLoaded] = useState(false);
  const [clientName, setClientName] = useState<string>('');
  const [loadingClient, setLoadingClient] = useState(false);

  // ─── New state ─────────────────────────────────────────────────────────────
  const [clientData, setClientData] = useState<ClientDetailResponse | null>(null);
  const [prefilledMovements, setPrefilledMovements] = useState<Movement[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('strength_linear_5x5');
  const [editingMovement, setEditingMovement] = useState<string | null>(null);
  const [editTarget, setEditTarget] = useState<string>('');
  const [editJump, setEditJump] = useState<string>('');
  // Client selection state (when wizard is opened without a clientId in URL)
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [clientSearch, setClientSearch] = useState('');
  const [loadingClients, setLoadingClients] = useState(false);

  // ─── Effects ──────────────────────────────────────────────────────────────

  useEffect(() => {
    fetchCalculationConstants()
      .then(() => setConstantsLoaded(true))
      .catch(() => setConstantsLoaded(true));
  }, []);

  useEffect(() => {
    if (currentStep === 'selectClient' && clients.length === 0) {
      setLoadingClients(true);
      listMyClients()
        .then(res => setClients(res.clients))
        .catch(() => {})
        .finally(() => setLoadingClients(false));
    }
  }, [currentStep]);

  useEffect(() => {
    if (selectedClientId) {
      setLoadingClient(true);
      getClientDetail(selectedClientId)
        .then(client => {
          setClientData(client);
          const basicInfo = client.profile?.basic_info ?? {};
          setClientName(`${basicInfo.first_name ?? 'Unknown'} ${basicInfo.last_name ?? 'Client'}`);

          // Build pre-filled movements from stored 1RMs
          const oneRepMaxes = (client.profile?.training_experience?.one_rep_maxes ?? {}) as Record<string, OneRepMax>;
          const prefilled: Movement[] = Object.entries(oneRepMaxes).map(([movName, data]) => ({
            id: movName,
            name: movName,
            oneRM: data.weight,
            eightyPercentRM: calculate80Percent(data.weight),
            maxRepsAt80: 0,
            weeklyJumpPercent: 0,
            weeklyJumpLbs: 0,
            rampUpPercent: 0,
            rampUpBaseLbs: 0,
            targetWeight: 0,
            fromProfile: true,
          }));
          setPrefilledMovements(prefilled);
        })
        .catch(err => console.error('Failed to load client details:', err))
        .finally(() => setLoadingClient(false));
    }
  }, [selectedClientId]);

  // ─── Program save ─────────────────────────────────────────────────────────

  const handleSaveProgram = async () => {
    setIsSaving(true);
    try {
      const programName = clientName
        ? `${clientName} - ${movements.map(m => m.name).join(', ')}`
        : `${movements.map(m => m.name).join(', ')} - 8 Week Program`;

      const programInputs = {
        builder_type: 'strength_linear_5x5',
        name: programName,
        description: clientName
          ? `Linear progression strength program for ${clientName}`
          : 'Linear progression strength program',
        movements: movements.map(m => ({
          name: m.name,
          one_rm: m.oneRM,
          max_reps_at_80_percent: m.maxRepsAt80,
          target_weight: m.targetWeight,
        })),
        duration_weeks: 8,
        days_per_week: 4,
        is_template: false,
        client_id: selectedClientId,
      };

      const savedProgram = await apiFetch<{ id: string; assignment_id?: string }>('/programs/', {
        method: 'POST',
        body: JSON.stringify(programInputs),
      });

      navigate(`/programs/draft/${savedProgram.id}?clientId=${selectedClientId}`);
    } catch (error) {
      setIsSaving(false);
      alert(t('programBuilder.step5.saveError', {
        error: error instanceof Error ? error.message : 'Unknown error',
      }));
    }
  };

  // ─── Movement helpers ─────────────────────────────────────────────────────

  const addMovement = (name: string) => {
    if (movements.length >= 4) { alert(t('programBuilder.step1.maxMovements')); return; }
    setMovements([...movements, {
      id: Date.now().toString(), name, oneRM: 0, eightyPercentRM: 0,
      maxRepsAt80: 0, weeklyJumpPercent: 0, weeklyJumpLbs: 0,
      rampUpPercent: 0, rampUpBaseLbs: 0, targetWeight: 0,
    }]);
  };

  const removeMovement = (id: string) => setMovements(movements.filter(m => m.id !== id));

  const updateMovement = (id: string, updates: Partial<Movement>) =>
    setMovements(movements.map(m => m.id === id ? { ...m, ...updates } : m));

  // ─── Step: selectClient ───────────────────────────────────────────────────

  const handleSelectClient = (clientId: string) => {
    setSelectedClientId(clientId);
    setCurrentStep('clientContext');
  };

  const handleBackToClientSelect = () => {
    setSelectedClientId(null);
    setClientData(null);
    setClientName('');
    setCurrentStep('selectClient');
    setClientSearch('');
  };

  const renderSelectClientStep = () => {
    if (loadingClients) {
      return (
        <div className="step-content">
          <div className="client-loading"><div className="spinner-sm" /><p>Loading clients…</p></div>
        </div>
      );
    }

    const filtered = clientSearch.trim()
      ? clients.filter(c => c.name.toLowerCase().includes(clientSearch.toLowerCase()) || c.email.toLowerCase().includes(clientSearch.toLowerCase()))
      : clients;

    return (
      <div className="step-content">
        <h2>Select a Client</h2>
        <p className="step-description">Choose the client this program is being built for.</p>

        <input
          type="search"
          className="search-input"
          placeholder="Search clients by name or email…"
          value={clientSearch}
          onChange={e => setClientSearch(e.target.value)}
          autoFocus
        />

        {filtered.length === 0 ? (
          <p style={{ color: '#888', marginTop: '2rem', textAlign: 'center' }}>
            {clients.length === 0 ? 'No clients found. Add clients first.' : `No clients match "${clientSearch}".`}
          </p>
        ) : (
          <div className="client-select-list">
            {filtered.map(c => (
              <button
                key={c.id}
                className="client-select-item"
                onClick={() => handleSelectClient(c.id)}
              >
                <div className="client-select-item-content">
                  <div className="client-select-info">
                    <div className="client-select-name">{c.name}</div>
                    <div className="client-select-email">{c.email}</div>
                  </div>
                  <span className="client-select-arrow">→</span>
                </div>
              </button>
            ))}
          </div>
        )}

        <div className="step-actions select-client-actions" style={{ marginTop: '2rem', display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <button
            className="tertiary-btn"
            onClick={() => navigate('/clients')}
          >
            ← Back to Clients
          </button>
        </div>
      </div>
    );
  };

  // ─── Step: clientContext ──────────────────────────────────────────────────

  const renderClientContextStep = () => {
    if (loadingClient || !clientData) {
      return (
        <div className="step-content">
          <div className="client-loading"><div className="spinner-sm" /><p>Loading client data…</p></div>
        </div>
      );
    }

    const profile = clientData.profile ?? {};
    const goal = profile.fitness_goals?.primary_goal ?? '';
    const experience = profile.training_experience?.overall_experience_level ?? '';
    const daysPerWeek = profile.training_preferences?.available_days_per_week;
    const oneRepMaxes = (profile.training_experience?.one_rep_maxes ?? {}) as Record<string, OneRepMax>;
    const has1RMs = Object.keys(oneRepMaxes).length > 0;

    return (
      <div className="step-content">
        <h2>Client Profile</h2>
        <p className="step-description">
          Review {clientName}'s profile before building their program.
          Existing 1RM data will be pre-filled in the following steps.
        </p>

        <div className="client-context-panel">
          <div className="client-context-grid">
            <div className="context-item">
              <span className="context-label">Client</span>
              <span className="context-value">{clientName}</span>
            </div>
            {goal && (
              <div className="context-item">
                <span className="context-label">Primary Goal</span>
                <span className="context-value">
                  <span className="goal-badge">{GOAL_LABELS[goal] ?? goal}</span>
                </span>
              </div>
            )}
            {experience && (
              <div className="context-item">
                <span className="context-label">Experience</span>
                <span className="context-value">{EXPERIENCE_LABELS[experience] ?? experience}</span>
              </div>
            )}
            {daysPerWeek != null && (
              <div className="context-item">
                <span className="context-label">Available Days / Week</span>
                <span className="context-value">{daysPerWeek} days</span>
              </div>
            )}
          </div>

          {daysPerWeek != null && daysPerWeek < 4 && (
            <div className="days-warning">
              The Strength Linear 5×5 template requires 4 days/week.
              This client has {daysPerWeek} day{daysPerWeek === 1 ? '' : 's'} available.
              Consider discussing with the client or choosing a different template.
            </div>
          )}

          {has1RMs ? (
            <div className="one-rep-max-section">
              <h4>Recorded 1RMs — will be pre-filled</h4>
              <table className="one-rep-max-table">
                <thead>
                  <tr><th>Exercise</th><th>Weight</th><th>Unit</th><th>Date</th></tr>
                </thead>
                <tbody>
                  {Object.entries(oneRepMaxes).map(([name, data]) => (
                    <tr key={name}>
                      <td>{name}</td>
                      <td>{(data as OneRepMax).weight}</td>
                      <td>{(data as OneRepMax).unit}</td>
                      <td>{(data as OneRepMax).tested_date ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="no-1rm-note">No 1RM records on file. You'll enter them manually in the next steps.</p>
          )}
        </div>

        <div className="step-actions context-actions">
          <button
            className="tertiary-btn"
            onClick={handleBackToClientSelect}
          >
            ← Back to Client Selection
          </button>
          <button
            className="secondary-btn"
            onClick={() => {
              setPrefilledMovements([]);
              setMovements([]);
              setCurrentStep('templateSelect');
            }}
          >
            Start Fresh (ignore profile data)
          </button>
          <button
            className="primary-btn"
            onClick={() => {
              setMovements(prefilledMovements);
              setCurrentStep('templateSelect');
            }}
          >
            {has1RMs ? `Build Program (pre-fill ${Object.keys(oneRepMaxes).length} movements)` : 'Build Program'}
          </button>
        </div>
      </div>
    );
  };

  // ─── Step: templateSelect ─────────────────────────────────────────────────

  const renderTemplateSelectStep = () => {
    const clientGoal = clientData?.profile?.fitness_goals?.primary_goal ?? '';
    const suggestedId = TEMPLATES.find(t => t.available && t.goals.includes(clientGoal))?.id
      ?? TEMPLATES.find(t => t.available)?.id
      ?? 'strength_linear_5x5';

    return (
      <div className="step-content">
        <h2>Select a Program Template</h2>
        <p className="step-description">
          {clientGoal
            ? `Based on ${clientName || "the client"}'s goal (${GOAL_LABELS[clientGoal] ?? clientGoal}), we recommend a template below.`
            : 'Choose a template to generate the training program.'}
        </p>

        <div className="template-grid">
          {TEMPLATES.map(tmpl => {
            const isSuggested = tmpl.id === suggestedId;
            const isSelected = selectedTemplate === tmpl.id;
            return (
              <div
                key={tmpl.id}
                className={[
                  'template-card',
                  tmpl.available ? 'available' : 'disabled',
                  isSuggested ? 'suggested' : '',
                  isSelected ? 'selected' : '',
                ].filter(Boolean).join(' ')}
                onClick={() => tmpl.available && setSelectedTemplate(tmpl.id)}
              >
                {isSuggested && <div className="suggested-ribbon">Suggested</div>}
                {!tmpl.available && <div className="coming-soon-badge">Coming Soon</div>}
                <div className="template-card-header">
                  <span className="template-tag" style={{ background: tmpl.tagColor }}>{tmpl.tag}</span>
                  <h3>{tmpl.name}</h3>
                </div>
                <p className="template-description">{tmpl.description}</p>
                <div className="template-meta">
                  <span>{tmpl.duration_weeks} weeks</span>
                  <span>·</span>
                  <span>{tmpl.days_per_week} days/wk</span>
                </div>
              </div>
            );
          })}
        </div>

        <div className="step-actions">
          {selectedClientId && (
            <button className="secondary-btn" onClick={() => setCurrentStep('clientContext')}>
              Back
            </button>
          )}
          <button
            className="primary-btn"
            onClick={() => setCurrentStep('movements')}
            disabled={!selectedTemplate}
          >
            Use this template →
          </button>
        </div>
      </div>
    );
  };

  // ─── Step: movements ──────────────────────────────────────────────────────

  const renderMovementsStep = () => (
    <div className="step-content">
      <h2>{t('programBuilder.step1.title')}</h2>
      <p className="step-description">{t('programBuilder.step1.description')}</p>

      <div className="movement-input">
        <input
          type="text"
          placeholder={t('programBuilder.step1.placeholder')}
          value={newMovementName}
          onChange={e => setNewMovementName(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && newMovementName.trim()) {
              addMovement(newMovementName.trim());
              setNewMovementName('');
            }
          }}
        />
        <button
          onClick={() => {
            if (newMovementName.trim()) { addMovement(newMovementName.trim()); setNewMovementName(''); }
          }}
          disabled={movements.length >= 4}
        >
          {t('programBuilder.step1.addButton')}
        </button>
      </div>

      <div className="movements-list">
        {movements.map(movement => (
          <div key={movement.id} className="movement-card">
            <span>{movement.name}</span>
            {movement.fromProfile && <span className="from-profile-badge">From profile</span>}
            <button className="remove-btn" onClick={() => removeMovement(movement.id)}>✕</button>
          </div>
        ))}
      </div>

      <div className="step-actions">
        <button className="secondary-btn" onClick={() => setCurrentStep('templateSelect')}>
          {t('programBuilder.step1.backButton') ?? 'Back'}
        </button>
        <button
          className="primary-btn"
          onClick={() => setCurrentStep('oneRM')}
          disabled={movements.length === 0}
        >
          {t('programBuilder.step1.nextButton')}
        </button>
      </div>
    </div>
  );

  // ─── Step: oneRM ──────────────────────────────────────────────────────────

  const renderOneRMStep = () => {
    const completedTests = movements.filter(m => m.oneRM > 0).length;
    const totalTests = movements.length;

    return (
      <div className="step-content">
        <div className="step-header-with-progress">
          <div>
            <h2>{t('programBuilder.step2.title')}</h2>
            <p className="step-description">{t('programBuilder.step2.description')}</p>
          </div>
          <div className="progress-badge">
            <span className="progress-count">{completedTests}/{totalTests}</span>
            <span className="progress-label">{t('programBuilder.step2.completed')}</span>
          </div>
        </div>

        <div className="instructions-box">
          <div className="instruction-header">
            <span className="instruction-icon">📋</span>
            <h3>{t('programBuilder.step2.whatIs1RM')}</h3>
          </div>
          <p>{t('programBuilder.step2.oneRMDefinition')}</p>
          <div className="instruction-tips">
            <h4>{t('programBuilder.step2.safetyTips')}</h4>
            <ul>
              <li>{t('programBuilder.step2.tip1')}</li>
              <li>{t('programBuilder.step2.tip2')}</li>
              <li>{t('programBuilder.step2.tip3')}</li>
              <li>{t('programBuilder.step2.tip4')}</li>
              <li>{t('programBuilder.step2.tip5')}</li>
              <li>{t('programBuilder.step2.tip6')}</li>
            </ul>
          </div>
          <div className="instruction-example">
            <strong>{t('programBuilder.step2.exampleProgression')}</strong>
            <div className="example-progression">
              <span>{t('programBuilder.step2.warmup')} → 135 lbs x 10</span>
              <span>→ 225 lbs x 5</span>
              <span>→ 315 lbs x 3</span>
              <span>→ 405 lbs x 1</span>
              <span>→ 450 lbs x 1 ✓ (1RM)</span>
            </div>
          </div>
        </div>

        <div className="test-section">
          <h3 className="section-title">{t('programBuilder.step2.enterResults')}</h3>
          <div className="movements-grid">
            {movements.map((movement, index) => (
              <div key={movement.id} className={`movement-test-card ${movement.oneRM > 0 ? 'completed' : ''}`}>
                <div className="card-header">
                  <div className="card-number">{index + 1}</div>
                  <h3>{movement.name}</h3>
                  {movement.oneRM > 0 && <span className="check-icon">✓</span>}
                </div>

                <div className="input-group">
                  <label>{t('programBuilder.step2.maxWeightLifted')}</label>
                  <div className="input-with-unit">
                    <input
                      type="number"
                      value={movement.oneRM || ''}
                      onChange={e => {
                        const value = e.target.value === '' ? 0 : Number(e.target.value);
                        updateMovement(movement.id, {
                          oneRM: value,
                          eightyPercentRM: calculate80Percent(value),
                        });
                      }}
                      placeholder={t('programBuilder.step2.placeholder')}
                      min="0"
                      step="5"
                    />
                    <span className="unit-label">lbs</span>
                  </div>
                  {movement.fromProfile && movement.oneRM > 0 && (
                    <p className="profile-source-note">Loaded from client profile</p>
                  )}
                </div>

                {movement.oneRM > 0 && (
                  <div className="calculation-result">
                    <div className="result-row">
                      <span className="result-label">{t('programBuilder.step2.eightyPercentOf1RM')}</span>
                      <strong className="result-value">{movement.eightyPercentRM} lbs</strong>
                    </div>
                    <p className="result-note">{t('programBuilder.step2.nextTestNote')}</p>
                  </div>
                )}

                {movement.oneRM === 0 && (
                  <div className="pending-message">
                    <span className="pending-icon">⏳</span>
                    <span>{t('programBuilder.step2.pendingInput')}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {completedTests > 0 && (
          <div className="progress-summary">
            {completedTests === totalTests ? (
              <div className="success-message">
                <span className="success-icon">✓</span>
                <span>{t('programBuilder.step2.allCompleted')}</span>
              </div>
            ) : (
              <div className="info-message">
                <span className="info-icon">ℹ️</span>
                <span>{t('programBuilder.step2.progress', { completed: completedTests, total: totalTests })}</span>
              </div>
            )}
          </div>
        )}

        <div className="step-actions">
          <button className="secondary-btn" onClick={() => setCurrentStep('movements')}>
            {t('programBuilder.step2.backButton')}
          </button>
          <button
            className="primary-btn"
            onClick={() => setCurrentStep('eightyPercentTest')}
            disabled={movements.some(m => m.oneRM === 0)}
          >
            {t('programBuilder.step2.nextButton')}
          </button>
        </div>
      </div>
    );
  };

  // ─── Step: eightyPercentTest ──────────────────────────────────────────────

  const renderEightyPercentStep = () => (
    <div className="step-content">
      <h2>{t('programBuilder.step3.title')}</h2>
      <p className="step-description">{t('programBuilder.step3.description')}</p>

      <div className="movements-grid">
        {movements.map(movement => (
          <div key={movement.id} className="movement-input-card">
            <h3>{movement.name}</h3>
            <div className="info-row">
              <span>80% 1RM:</span>
              <strong>{movement.eightyPercentRM} lbs</strong>
            </div>
            <div className="input-group">
              <label>{t('programBuilder.step3.maxRepsPerformed')}</label>
              <input
                type="number"
                value={movement.maxRepsAt80 || ''}
                onChange={async e => {
                  const value = e.target.value === '' ? 0 : Number(e.target.value);
                  if (value > 0 && value <= 20) {
                    const jumpData = await calculateWeeklyJump(value, movement.oneRM);
                    const rampUpData = await calculateRampUp(value, movement.oneRM);
                    updateMovement(movement.id, {
                      maxRepsAt80: value,
                      weeklyJumpPercent: jumpData.percent,
                      weeklyJumpLbs: jumpData.lbs,
                      rampUpPercent: rampUpData.percent,
                      rampUpBaseLbs: rampUpData.baseLbs,
                    });
                  } else {
                    updateMovement(movement.id, { maxRepsAt80: value });
                  }
                }}
                placeholder={t('programBuilder.step3.placeholder')}
                min="1"
                max="20"
              />
            </div>
            {movement.maxRepsAt80 > 0 && (
              <div className="calculations">
                <div className="calc-item">
                  <span>{t('programBuilder.step3.weeklyJump')}</span>
                  <strong>{movement.weeklyJumpPercent}% ({movement.weeklyJumpLbs} lbs)</strong>
                </div>
                <div className="calc-item">
                  <span>{t('programBuilder.step3.rampUpBase')}</span>
                  <strong>{movement.rampUpPercent}% ({movement.rampUpBaseLbs} lbs)</strong>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="step-actions">
        <button className="secondary-btn" onClick={() => setCurrentStep('oneRM')}>
          {t('programBuilder.step3.backButton')}
        </button>
        <button
          className="primary-btn"
          onClick={() => setCurrentStep('fiveRMTest')}
          disabled={movements.some(m => m.maxRepsAt80 === 0)}
        >
          {t('programBuilder.step3.nextButton')}
        </button>
      </div>
    </div>
  );

  // ─── Step: fiveRMTest ─────────────────────────────────────────────────────

  const renderFiveRMTest = () => (
    <div className="step-content">
      <h2>{t('programBuilder.step4.title')}</h2>
      <p className="step-description">{t('programBuilder.step4.description')}</p>

      <div className="movements-selection">
        {movements.map(movement => (
          <button
            key={movement.id}
            className={`movement-select-btn ${selectedMovement?.id === movement.id ? 'selected' : ''}`}
            onClick={() => setSelectedMovement(movement)}
          >
            {movement.name}
          </button>
        ))}
      </div>

      {selectedMovement && (
        <div className="test-protocol">
          <h3>{t('programBuilder.step4.testProtocol')} - {selectedMovement.name}</h3>
          <div className="test-info">
            <div className="info-card">
              <label>{t('programBuilder.step4.baseWeight')}</label>
              <strong>{selectedMovement.rampUpBaseLbs} lbs</strong>
            </div>
            <div className="info-card">
              <label>{t('programBuilder.step4.incrementPerSet')}</label>
              <strong>{selectedMovement.weeklyJumpLbs} lbs</strong>
            </div>
          </div>
          <div className="test-instructions">
            <h4>{t('programBuilder.step4.instructions')}</h4>
            <ol>
              <li>{t('programBuilder.step4.instruction1', { weight: selectedMovement.rampUpBaseLbs })}</li>
              <li>{t('programBuilder.step4.instruction2')}</li>
              <li>{t('programBuilder.step4.instruction3', { weight: selectedMovement.weeklyJumpLbs })}</li>
              <li>{t('programBuilder.step4.instruction4')}</li>
              <li>{t('programBuilder.step4.instruction5')}</li>
            </ol>
            <p className="note">
              <strong>{t('programBuilder.step4.note')}</strong> {t('programBuilder.step4.noteText')}
            </p>
          </div>
          <div className="test-progression">
            <h4>{t('programBuilder.step4.suggestedProgression')}</h4>
            <div className="progression-list">
              {Array.from({ length: 8 }, (_, i) => {
                const weight = selectedMovement.rampUpBaseLbs + (i * selectedMovement.weeklyJumpLbs);
                return (
                  <div key={i} className="progression-item">
                    <span className="set-number">{t('programBuilder.step4.set')} {i + 1}</span>
                    <span className="weight">{weight} lbs x 5</span>
                    {i < 7 && <span className="rest">{t('programBuilder.step4.rest')}</span>}
                  </div>
                );
              })}
            </div>
          </div>
          <div className="target-input">
            <label>{t('programBuilder.step4.targetAchieved')}</label>
            <div className="target-input-group">
              <input
                type="number"
                value={movements.find(m => m.id === selectedMovement.id)?.targetWeight || ''}
                onChange={e => {
                  const value = e.target.value === '' ? 0 : Number(e.target.value);
                  updateMovement(selectedMovement.id, { targetWeight: value });
                  setSelectedMovement({ ...selectedMovement, targetWeight: value });
                }}
                placeholder={t('programBuilder.step4.placeholder')}
                min="0"
                step="5"
              />
              <span>lbs</span>
            </div>
          </div>
        </div>
      )}

      <div className="step-actions">
        <button className="secondary-btn" onClick={() => setCurrentStep('eightyPercentTest')}>
          {t('programBuilder.step4.backButton')}
        </button>
        <button
          className="primary-btn"
          onClick={() => setCurrentStep('program')}
          disabled={movements.some(m => m.targetWeight === 0)}
        >
          {t('programBuilder.step4.nextButton')}
        </button>
      </div>
    </div>
  );

  // ─── Week tabs ────────────────────────────────────────────────────────────

  const renderWeekTabs = () => {
    const handleWeekClick = (week: number) => { setLastSingleWeek(week); setSelectedWeek(week); };
    const handleViewAllToggle = () => {
      if (selectedWeek === 'all') { setSelectedWeek(lastSingleWeek); }
      else { setLastSingleWeek(selectedWeek as number); setSelectedWeek('all'); }
    };
    return (
      <div className="week-tabs-container">
        <div className="week-tabs">
          {[1, 2, 3, 4, 5, 6, 7, 8].map(week => (
            <button
              key={week}
              className={`week-tab ${selectedWeek === week ? 'active' : ''}`}
              onClick={() => handleWeekClick(week)}
            >
              {t('programBuilder.step5.week')} {week}
            </button>
          ))}
          <button
            className={`week-tab view-all ${selectedWeek === 'all' ? 'active' : ''}`}
            onClick={handleViewAllToggle}
          >
            {selectedWeek === 'all' ? `← ${t('programBuilder.step5.week')} ${lastSingleWeek}` : 'View All'}
          </button>
        </div>
      </div>
    );
  };

  // ─── Step: program ────────────────────────────────────────────────────────

  const renderProgramStep = () => {
    const getLightWeight = (heavyWeight: number) => Math.round(heavyWeight * 0.8);

    return (
      <div className="step-content">
        <h2>{t('programBuilder.step5.title')}</h2>
        <p className="step-description">{t('programBuilder.step5.description')}</p>

        {renderWeekTabs()}

        <div className="program-info-box">
          <h3>Session Structure</h3>
          <p>Each exercise is performed 4 times per week, alternating between <strong>HEAVY</strong> and <strong>LIGHT</strong> days</p>
          <ul>
            <li><strong>Session 1:</strong> All exercises HEAVY</li>
            <li><strong>Session 2:</strong> All exercises light (80% of heavy weight)</li>
            <li><strong>Session 3:</strong> All exercises HEAVY</li>
            <li><strong>Session 4:</strong> All exercises light (80% of heavy weight)</li>
          </ul>
          <p className="note">Pattern for each exercise: HEAVY - light - HEAVY - light</p>
        </div>

        {/* Movement summaries with inline editing */}
        <div className="movements-summary">
          <h3>{t('programBuilder.step5.programSummary')}</h3>
          {movements.map(movement => (
            <div key={movement.id} className="program-card">
              <div className="program-card-header">
                <h4>{movement.name}</h4>
                {editingMovement !== movement.id && (
                  <button
                    className="edit-program-btn"
                    title="Adjust target weight and weekly jump"
                    onClick={() => {
                      setEditingMovement(movement.id);
                      setEditTarget(String(movement.targetWeight));
                      setEditJump(String(movement.weeklyJumpLbs));
                    }}
                  >
                    ✏️ Edit
                  </button>
                )}
              </div>

              {editingMovement === movement.id ? (
                <div className="movement-edit-form">
                  <div className="edit-field">
                    <label>5×5 Target Weight (lbs)</label>
                    <input
                      type="number"
                      value={editTarget}
                      onChange={e => setEditTarget(e.target.value)}
                      step="5"
                      min="0"
                      autoFocus
                    />
                  </div>
                  <div className="edit-field">
                    <label>Weekly Jump (lbs)</label>
                    <input
                      type="number"
                      value={editJump}
                      onChange={e => setEditJump(e.target.value)}
                      step="5"
                      min="0"
                    />
                  </div>
                  <div className="edit-actions">
                    <button
                      className="edit-confirm-btn"
                      onClick={() => {
                        updateMovement(movement.id, {
                          targetWeight: Number(editTarget) || movement.targetWeight,
                          weeklyJumpLbs: Number(editJump) || movement.weeklyJumpLbs,
                        });
                        setEditingMovement(null);
                      }}
                    >
                      Apply
                    </button>
                    <button className="edit-cancel-btn" onClick={() => setEditingMovement(null)}>
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="summary-grid">
                  <div className="summary-detail-item">
                    <span className="summary-label">{t('programBuilder.step5.oneRM')}</span>
                    <span className="summary-value">{movement.oneRM} lbs</span>
                  </div>
                  <div className="summary-detail-item">
                    <span className="summary-label">{t('programBuilder.step5.weeklyJump')}</span>
                    <span className="summary-value">{movement.weeklyJumpLbs} lbs</span>
                  </div>
                  <div className="summary-detail-item highlight">
                    <span className="summary-label">{t('programBuilder.step5.target5x5')}</span>
                    <span className="summary-value">{movement.targetWeight} lbs</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 8-week reference table */}
        <div className="quick-reference">
          <h3>8-Week Progression Overview</h3>
          <div className="reference-table-container">
            <table className="reference-table">
              <thead>
                <tr>
                  <th>Movement</th>
                  {[1,2,3,4,5,6,7,8].map(w => <th key={w}>{t('programBuilder.step5.week')} {w}</th>)}
                </tr>
              </thead>
              <tbody>
                {movements.map(movement => {
                  const weights = [
                    movement.targetWeight - (4 * movement.weeklyJumpLbs),
                    movement.targetWeight - (3 * movement.weeklyJumpLbs),
                    movement.targetWeight - (2 * movement.weeklyJumpLbs),
                    movement.targetWeight - movement.weeklyJumpLbs,
                    movement.targetWeight,
                    movement.targetWeight + movement.weeklyJumpLbs,
                    movement.targetWeight + (2 * movement.weeklyJumpLbs),
                  ];
                  return (
                    <tr key={movement.id}>
                      <td className="movement-name-cell">{movement.name}</td>
                      {weights.map((w, i) => (
                        <td key={i} className={`weight-cell ${i === 4 ? 'highlight-cell' : ''}`}>{w} lbs</td>
                      ))}
                      <td className="test-cell">{t('programBuilder.step5.test1RM')}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="reference-note">
            <strong>Note:</strong> Weeks 1–5 use 5×5, Week 6 uses 3×3, Week 7 uses 2×2, Week 8 is testing week
          </p>
        </div>

        {/* Weekly schedule */}
        <div className="sessions-program">
          <h3>Weekly Training Schedule</h3>

          {[1, 2, 3, 4, 5].filter(week => selectedWeek === 'all' || selectedWeek === week).map(week => (
            <div key={week} className="week-block">
              <h4>{t('programBuilder.step5.week')} {week}</h4>
              <div className="sessions-grid">
                {[
                  { label: 'Session 1 - Heavy Day', day: 'Monday', isHeavy: true },
                  { label: 'Session 2 - Light Day', day: 'Wednesday', isHeavy: false },
                  { label: 'Session 3 - Heavy Day', day: 'Friday', isHeavy: true },
                  { label: 'Session 4 - Light Day', day: 'Saturday', isHeavy: false },
                ].map(session => (
                  <div key={session.label} className="session-card">
                    <div className="session-header">
                      <span className="session-title">{session.label}</span>
                      <span className="session-day">{session.day}</span>
                    </div>
                    <div className="session-exercises">
                      {movements.map(movement => {
                        const heavyWeight = movement.targetWeight - ((5 - week) * movement.weeklyJumpLbs);
                        const displayWeight = session.isHeavy ? heavyWeight : getLightWeight(heavyWeight);
                        const percentage = Math.round((displayWeight / movement.oneRM) * 100);
                        return (
                          <div key={movement.id} className={`exercise ${session.isHeavy ? 'heavy-exercise' : 'light-exercise'}`}>
                            <span className="exercise-name">{session.isHeavy ? movement.name.toUpperCase() : movement.name.toLowerCase()}</span>
                            <span className="exercise-protocol">5x5</span>
                            <span className="exercise-weight">{displayWeight} lbs <span className="percentage">({percentage}%)</span></span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {(selectedWeek === 'all' || selectedWeek === 6) && (
            <div className="week-block">
              <h4>{t('programBuilder.step5.week')} 6</h4>
              <div className="sessions-grid">
                {[
                  { label: 'Session 1 - Heavy Day', day: 'Monday', isHeavy: true },
                  { label: 'Session 2 - Light Day', day: 'Wednesday', isHeavy: false },
                  { label: 'Session 3 - Heavy Day', day: 'Friday', isHeavy: true },
                  { label: 'Session 4 - Light Day', day: 'Saturday', isHeavy: false },
                ].map(session => (
                  <div key={session.label} className="session-card">
                    <div className="session-header">
                      <span className="session-title">{session.label}</span>
                      <span className="session-day">{session.day}</span>
                    </div>
                    <div className="session-exercises">
                      {movements.map(movement => {
                        const heavyWeight = movement.targetWeight + movement.weeklyJumpLbs;
                        const displayWeight = session.isHeavy ? heavyWeight : getLightWeight(heavyWeight);
                        const percentage = Math.round((displayWeight / movement.oneRM) * 100);
                        return (
                          <div key={movement.id} className={`exercise ${session.isHeavy ? 'heavy-exercise' : 'light-exercise'}`}>
                            <span className="exercise-name">{session.isHeavy ? movement.name.toUpperCase() : movement.name.toLowerCase()}</span>
                            <span className="exercise-protocol">3x3</span>
                            <span className="exercise-weight">{displayWeight} lbs <span className="percentage">({percentage}%)</span></span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(selectedWeek === 'all' || selectedWeek === 7) && (
            <div className="week-block">
              <h4>{t('programBuilder.step5.week')} 7</h4>
              <div className="sessions-grid">
                {[
                  { label: 'Session 1 - Heavy Day', day: 'Monday', isHeavy: true },
                  { label: 'Session 2 - Light Day', day: 'Wednesday', isHeavy: false },
                  { label: 'Session 3 - Heavy Day', day: 'Friday', isHeavy: true },
                  { label: 'Session 4 - Light Day', day: 'Saturday', isHeavy: false },
                ].map(session => (
                  <div key={session.label} className="session-card">
                    <div className="session-header">
                      <span className="session-title">{session.label}</span>
                      <span className="session-day">{session.day}</span>
                    </div>
                    <div className="session-exercises">
                      {movements.map(movement => {
                        const heavyWeight = movement.targetWeight + (movement.weeklyJumpLbs * 2);
                        const displayWeight = session.isHeavy ? heavyWeight : getLightWeight(heavyWeight);
                        const percentage = Math.round((displayWeight / movement.oneRM) * 100);
                        return (
                          <div key={movement.id} className={`exercise ${session.isHeavy ? 'heavy-exercise' : 'light-exercise'}`}>
                            <span className="exercise-name">{session.isHeavy ? movement.name.toUpperCase() : movement.name.toLowerCase()}</span>
                            <span className="exercise-protocol">2x2</span>
                            <span className="exercise-weight">{displayWeight} lbs <span className="percentage">({percentage}%)</span></span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(selectedWeek === 'all' || selectedWeek === 8) && (
            <div className="week-block test-week">
              <h4>{t('programBuilder.step5.week')} 8 - {t('programBuilder.step5.testWeek')}</h4>
              <div className="test-week-content">
                <div className="test-day-card">
                  <div className="test-day-header">
                    <span className="test-icon">🎯</span>
                    <h5>1RM Test Day</h5>
                  </div>
                  <div className="test-movements">
                    {movements.map(movement => (
                      <div key={movement.id} className="test-movement-item">
                        <span className="test-movement-name">{movement.name.toUpperCase()}</span>
                        <span className="test-movement-action">Test New 1RM</span>
                        <span className="test-movement-previous">Previous: {movement.oneRM} lbs</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="test-week-instructions">
                  <h5>Testing Week Protocol</h5>
                  <ul>
                    <li><strong>Rest 2–3 days</strong> before your test day to ensure full recovery</li>
                    <li><strong>Test 1RM</strong> for all movements using proper warm-up protocol</li>
                    <li><strong>Rest for the remainder</strong> of the week after testing</li>
                    <li>Record your new 1RM values to track progress</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="step-actions">
          <button className="secondary-btn" onClick={() => setCurrentStep('fiveRMTest')}>
            {t('programBuilder.step5.backButton')}
          </button>
          <button className="primary-btn" onClick={handleSaveProgram} disabled={isSaving}>
            {isSaving ? t('programBuilder.step5.saving') : t('programBuilder.step5.saveButton')}
          </button>
        </div>
      </div>
    );
  };

  // ─── Step indicator ───────────────────────────────────────────────────────

  const renderStepIndicator = () => {
    const steps = [
      { key: 'templateSelect', label: 'Template' },
      { key: 'movements', label: t('programBuilder.steps.movements') },
      { key: 'oneRM', label: t('programBuilder.steps.oneRM') },
      { key: 'eightyPercentTest', label: t('programBuilder.steps.eightyPercent') },
      { key: 'fiveRMTest', label: t('programBuilder.steps.fiveRM') },
      { key: 'program', label: t('programBuilder.steps.program') },
    ];

    // Determine step order for progress highlight
    const stepOrder: Step[] = ['clientContext', 'templateSelect', 'movements', 'oneRM', 'eightyPercentTest', 'fiveRMTest', 'program'];
    const currentIdx = stepOrder.indexOf(currentStep);

    return (
      <div className="step-indicator">
        {steps.map((step, index) => {
          const stepIdx = stepOrder.indexOf(step.key as Step);
          const isActive = currentStep === step.key;
          const isCompleted = stepIdx < currentIdx;
          return (
            <div key={step.key} className={`step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}>
              <div className="step-number">{isCompleted ? '✓' : index + 1}</div>
              <div className="step-label">{step.label}</div>
            </div>
          );
        })}
      </div>
    );
  };

  // ─── Router ───────────────────────────────────────────────────────────────

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 'selectClient':    return renderSelectClientStep();
      case 'clientContext':    return renderClientContextStep();
      case 'templateSelect':  return renderTemplateSelectStep();
      case 'movements':       return renderMovementsStep();
      case 'oneRM':           return renderOneRMStep();
      case 'eightyPercentTest': return renderEightyPercentStep();
      case 'fiveRMTest':      return renderFiveRMTest();
      case 'program':         return renderProgramStep();
      default:                return renderTemplateSelectStep();
    }
  };

  // ─── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="program-builder">
      <div className="builder-header">
        <h1>{t('programBuilder.title')}</h1>
        <p>{t('programBuilder.subtitle')}</p>
        {selectedClientId && clientName && (
          <div className="client-indicator">
            <span className="client-label">Building for:</span>
            <span className="client-name">{clientName}</span>
            <button className="btn-link" onClick={() => navigate(`/clients/${selectedClientId}`)} style={{ marginLeft: '1rem' }}>
              View Client →
            </button>
          </div>
        )}
        {selectedClientId && loadingClient && (
          <div className="client-indicator">
            <span className="client-label">Loading client…</span>
          </div>
        )}
      </div>

      {currentStep !== 'clientContext' && currentStep !== 'selectClient' && renderStepIndicator()}
      {constantsLoaded ? renderCurrentStep() : (
        <div className="step-content">
          <div className="client-loading"><div className="spinner-sm" /><p>Loading…</p></div>
        </div>
      )}

    </div>
  );
}
