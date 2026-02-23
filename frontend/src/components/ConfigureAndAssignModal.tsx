import { useState, useEffect, useMemo } from 'react';
import {
  listPrograms,
  getProgramDetail,
  generateForClient,
  type ProgramSummary,
  type MovementParam,
} from '../services/programs';
import { listMyClients, getClientDetail, type ClientSummary } from '../services/clients';
import { ApiError } from '../services/api';
import './AssignProgramModal.css';

interface Props {
  templateId?: string;
  templateName?: string;
  clientId?: string;
  clientName?: string;
  /** Movements pre-configured in the wizard. When provided, the configure step
   *  shows a read-only summary instead of editable inputs. */
  presetMovements?: MovementParam[];
  onClose: () => void;
  onGenerated: (programId: string, clientId: string) => void;
}

type Step = 'pick_client' | 'pick_template' | 'configure_params' | 'generating';

interface MovementRow extends MovementParam {
  name: string;
}

export default function ConfigureAndAssignModal({
  templateId: initialTemplateId,
  templateName: initialTemplateName,
  clientId: initialClientId,
  clientName: initialClientName,
  presetMovements,
  onClose,
  onGenerated,
}: Props) {
  // Determine initial step based on pre-supplied props
  const initialStep: Step = initialClientId
    ? initialTemplateId
      ? 'configure_params'
      : 'pick_template'
    : 'pick_client';

  const [step, setStep] = useState<Step>(initialStep);

  // Client selection
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [clientSearch, setClientSearch] = useState('');
  const [loadingClients, setLoadingClients] = useState(false);
  const [selectedClientId, setSelectedClientId] = useState<string>(initialClientId || '');
  const [selectedClientName, setSelectedClientName] = useState<string>(initialClientName || '');

  // Template selection
  const [templates, setTemplates] = useState<ProgramSummary[]>([]);
  const [templateSearch, setTemplateSearch] = useState('');
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>(initialTemplateId || '');
  const [selectedTemplateName, setSelectedTemplateName] = useState<string>(initialTemplateName || '');
  const [selectedTemplateMeta, setSelectedTemplateMeta] = useState<{
    duration_weeks: number;
    days_per_week: number;
  } | null>(null);

  // Configure params
  const [movements, setMovements] = useState<MovementRow[]>([]);
  const [loadingParams, setLoadingParams] = useState(false);
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Load clients when on pick_client step
  useEffect(() => {
    if (step === 'pick_client') {
      setLoadingClients(true);
      listMyClients()
        .then(res => setClients(res.clients))
        .catch(() => {})
        .finally(() => setLoadingClients(false));
    }
  }, [step]);

  // Load templates when on pick_template step
  useEffect(() => {
    if (step === 'pick_template') {
      setLoadingTemplates(true);
      listPrograms({ is_template: true })
        .then(res => setTemplates(res.programs))
        .catch(() => {})
        .finally(() => setLoadingTemplates(false));
    }
  }, [step]);

  // Load template detail + (optionally) client 1RMs when on configure_params step
  useEffect(() => {
    if (step !== 'configure_params' || !selectedTemplateId || !selectedClientId) return;

    setLoadingParams(true);
    setError(null);

    if (presetMovements && presetMovements.length > 0) {
      // Movements already configured in the wizard — only fetch template meta for display
      getProgramDetail(selectedTemplateId)
        .then(tmpl => {
          setSelectedTemplateMeta({ duration_weeks: tmpl.duration_weeks, days_per_week: tmpl.days_per_week });
          setMovements(presetMovements.map(m => ({ ...m })));
        })
        .catch(() => setError('Failed to load program details. Please try again.'))
        .finally(() => setLoadingParams(false));
    } else {
      // Normal flow: fetch template movement names + client 1RMs
      Promise.all([
        getProgramDetail(selectedTemplateId),
        getClientDetail(selectedClientId),
      ])
        .then(([tmpl, client]) => {
          const inputData = tmpl.input_data as { movements?: Array<{ name: string }> };
          const movementNames: string[] = inputData?.movements?.map(m => m.name) || [];

          const orms = client.profile?.training_experience?.one_rep_maxes || {};

          const rows: MovementRow[] = movementNames.map(name => {
            const key = name.toLowerCase();
            const existing = Object.entries(orms).find(([k]) => k.toLowerCase().includes(key) || key.includes(k.toLowerCase()));
            const existingOrm = existing ? existing[1] : null;

            return {
              name,
              one_rm: existingOrm ? existingOrm.weight : 0,
              max_reps_at_80_percent: 5,
              target_weight: existingOrm ? Math.round(existingOrm.weight * 0.8) : 0,
            };
          });

          setSelectedTemplateMeta({ duration_weeks: tmpl.duration_weeks, days_per_week: tmpl.days_per_week });
          setMovements(rows);
        })
        .catch(() => setError('Failed to load program details. Please try again.'))
        .finally(() => setLoadingParams(false));
    }
  }, [step, selectedTemplateId, selectedClientId, presetMovements]);

  const filteredClients = useMemo(() => {
    if (!clientSearch.trim()) return clients;
    const q = clientSearch.toLowerCase();
    return clients.filter(c => c.name.toLowerCase().includes(q) || c.email.toLowerCase().includes(q));
  }, [clients, clientSearch]);

  const filteredTemplates = useMemo(() => {
    if (!templateSearch.trim()) return templates;
    const q = templateSearch.toLowerCase();
    return templates.filter(t => t.name.toLowerCase().includes(q));
  }, [templates, templateSearch]);

  const updateMovement = (index: number, field: keyof MovementRow, value: number) => {
    setMovements(prev => prev.map((m, i) => i === index ? { ...m, [field]: value } : m));
  };

  const handleSelectClient = (client: ClientSummary) => {
    setSelectedClientId(client.id);
    setSelectedClientName(client.name);
    if (initialTemplateId) {
      setStep('configure_params');
    } else {
      setStep('pick_template');
    }
  };

  const handleSelectTemplate = (template: ProgramSummary) => {
    setSelectedTemplateId(template.id);
    setSelectedTemplateName(template.name);
    setStep('configure_params');
  };

  const handleGenerate = async () => {
    setError(null);
    for (const m of movements) {
      if (!m.one_rm || m.one_rm <= 0) {
        setError(`Please enter a valid 1RM for ${m.name}.`);
        return;
      }
      if (!m.target_weight || m.target_weight <= 0) {
        setError(`Please enter a valid target weight for ${m.name}.`);
        return;
      }
    }

    setStep('generating');
    try {
      const result = await generateForClient(selectedTemplateId, {
        client_id: selectedClientId,
        movements,
        start_date: startDate || undefined,
        notes: notes.trim() || undefined,
      });
      onGenerated(result.program_id, result.client_id);
    } catch (err) {
      setStep('configure_params');
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to generate program. Please try again.');
      }
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content assign-modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>
            {step === 'pick_client' && 'Select Client'}
            {step === 'pick_template' && 'Select Program Template'}
            {step === 'configure_params' && 'Configure Program'}
            {step === 'generating' && 'Generating Program...'}
          </h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {/* Step: pick_client */}
        {step === 'pick_client' && (
          <div className="modal-body">
            <p className="form-hint">Select a client to configure a program for.</p>
            <input
              type="search"
              className="assign-search-input"
              placeholder="Search clients..."
              value={clientSearch}
              onChange={e => setClientSearch(e.target.value)}
              autoFocus
            />
            {loadingClients ? (
              <div className="assign-loading"><div className="spinner" /><p>Loading clients...</p></div>
            ) : filteredClients.length === 0 ? (
              <div className="assign-empty">
                {clients.length === 0
                  ? <p>No clients found. Add clients first.</p>
                  : <p>No clients match "{clientSearch}".</p>
                }
              </div>
            ) : (
              <div className="assign-program-list">
                {filteredClients.map(client => (
                  <button
                    key={client.id}
                    className="assign-program-item"
                    onClick={() => handleSelectClient(client)}
                  >
                    <div className="assign-program-info">
                      <span className="assign-program-name">{client.name}</span>
                      <span className="assign-program-meta">{client.email}</span>
                    </div>
                    <span className="assign-arrow">›</span>
                  </button>
                ))}
              </div>
            )}
            <div className="modal-footer">
              <button className="btn-secondary" onClick={onClose}>Cancel</button>
            </div>
          </div>
        )}

        {/* Step: pick_template */}
        {step === 'pick_template' && (
          <div className="modal-body">
            <div className="confirm-program-banner" style={{ marginBottom: '1rem' }}>
              <span className="confirm-label">Client</span>
              <strong>{selectedClientName}</strong>
            </div>
            <input
              type="search"
              className="assign-search-input"
              placeholder="Search templates..."
              value={templateSearch}
              onChange={e => setTemplateSearch(e.target.value)}
              autoFocus
            />
            {loadingTemplates ? (
              <div className="assign-loading"><div className="spinner" /><p>Loading templates...</p></div>
            ) : filteredTemplates.length === 0 ? (
              <div className="assign-empty">
                {templates.length === 0
                  ? <p>No program templates. Build one first in the Programs Library.</p>
                  : <p>No templates match "{templateSearch}".</p>
                }
              </div>
            ) : (
              <div className="assign-program-list">
                {filteredTemplates.map(tmpl => (
                  <button
                    key={tmpl.id}
                    className="assign-program-item"
                    onClick={() => handleSelectTemplate(tmpl)}
                  >
                    <div className="assign-program-info">
                      <span className="assign-program-name">{tmpl.name}</span>
                      <span className="assign-program-meta">
                        {tmpl.duration_weeks} wks · {tmpl.days_per_week} days/wk
                        {tmpl.times_assigned > 0 && ` · Assigned ${tmpl.times_assigned}x`}
                      </span>
                    </div>
                    <span className="assign-arrow">›</span>
                  </button>
                ))}
              </div>
            )}
            <div className="modal-footer">
              {!initialClientId && (
                <button className="btn-secondary" onClick={() => setStep('pick_client')}>Back</button>
              )}
              <button className="btn-secondary" onClick={onClose}>Cancel</button>
            </div>
          </div>
        )}

        {/* Step: configure_params */}
        {step === 'configure_params' && (
          <div className="modal-body">
            <div className="confirm-program-banner">
              <span className="confirm-label">Program for {selectedClientName}</span>
              <strong>{selectedTemplateName}</strong>
              {selectedTemplateMeta && (
                <span className="confirm-meta">
                  {selectedTemplateMeta.duration_weeks} weeks · {selectedTemplateMeta.days_per_week} days/week
                </span>
              )}
            </div>

            {error && (
              <div style={{ color: '#c0392b', background: '#fdf0f0', padding: '0.75rem 1rem', borderRadius: '6px', marginBottom: '1rem', fontSize: '0.9rem' }}>
                {error}
              </div>
            )}

            {loadingParams ? (
              <div className="assign-loading"><div className="spinner" /><p>Loading parameters...</p></div>
            ) : (
              <>
                {presetMovements && presetMovements.length > 0 ? (
                  <>
                    <p className="form-hint" style={{ marginBottom: '0.75rem' }}>
                      Parameters from the program wizard. You can adjust weights after generating the draft.
                    </p>

                    {/* Read-only movement summary */}
                    <div style={{ overflowX: 'auto', marginBottom: '1.25rem' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                        <thead>
                          <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #e9ecef' }}>
                            <th style={{ padding: '0.6rem 0.75rem', textAlign: 'left', fontWeight: 600 }}>Movement</th>
                            <th style={{ padding: '0.6rem 0.75rem', textAlign: 'center', fontWeight: 600 }}>1RM (lbs)</th>
                            <th style={{ padding: '0.6rem 0.75rem', textAlign: 'center', fontWeight: 600 }}>Max reps @ 80%</th>
                            <th style={{ padding: '0.6rem 0.75rem', textAlign: 'center', fontWeight: 600 }}>Target wt (lbs)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {movements.map(m => (
                            <tr key={m.name} style={{ borderBottom: '1px solid #f0f0f0' }}>
                              <td style={{ padding: '0.6rem 0.75rem', fontWeight: 500 }}>{m.name}</td>
                              <td style={{ padding: '0.6rem 0.5rem', textAlign: 'center', color: '#444' }}>{m.one_rm} lbs</td>
                              <td style={{ padding: '0.6rem 0.5rem', textAlign: 'center', color: '#444' }}>{m.max_reps_at_80_percent}</td>
                              <td style={{ padding: '0.6rem 0.5rem', textAlign: 'center', color: '#444' }}>{m.target_weight} lbs</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                ) : (
                  <>
                    <p className="form-hint" style={{ marginBottom: '0.75rem' }}>Set client-specific parameters for each movement.</p>

                    {/* Editable movement params table */}
                    <div style={{ overflowX: 'auto', marginBottom: '1.25rem' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                        <thead>
                          <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #e9ecef' }}>
                            <th style={{ padding: '0.6rem 0.75rem', textAlign: 'left', fontWeight: 600 }}>Movement</th>
                            <th style={{ padding: '0.6rem 0.75rem', textAlign: 'center', fontWeight: 600 }}>1RM (lbs)</th>
                            <th style={{ padding: '0.6rem 0.75rem', textAlign: 'center', fontWeight: 600 }}>Max reps @ 80%</th>
                            <th style={{ padding: '0.6rem 0.75rem', textAlign: 'center', fontWeight: 600 }}>Target wt (lbs)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {movements.map((m, i) => (
                            <tr key={m.name} style={{ borderBottom: '1px solid #f0f0f0' }}>
                              <td style={{ padding: '0.6rem 0.75rem', fontWeight: 500 }}>{m.name}</td>
                              <td style={{ padding: '0.4rem 0.5rem', textAlign: 'center' }}>
                                <input
                                  type="number"
                                  min={1}
                                  step={5}
                                  value={m.one_rm || ''}
                                  onChange={e => updateMovement(i, 'one_rm', parseFloat(e.target.value) || 0)}
                                  style={{ width: '80px', padding: '0.4rem 0.5rem', border: '1px solid #ddd', borderRadius: '6px', textAlign: 'center', fontSize: '0.9rem' }}
                                />
                              </td>
                              <td style={{ padding: '0.4rem 0.5rem', textAlign: 'center' }}>
                                <input
                                  type="number"
                                  min={1}
                                  max={20}
                                  step={1}
                                  value={m.max_reps_at_80_percent || ''}
                                  onChange={e => updateMovement(i, 'max_reps_at_80_percent', parseInt(e.target.value) || 1)}
                                  style={{ width: '70px', padding: '0.4rem 0.5rem', border: '1px solid #ddd', borderRadius: '6px', textAlign: 'center', fontSize: '0.9rem' }}
                                />
                              </td>
                              <td style={{ padding: '0.4rem 0.5rem', textAlign: 'center' }}>
                                <input
                                  type="number"
                                  min={1}
                                  step={5}
                                  value={m.target_weight || ''}
                                  onChange={e => updateMovement(i, 'target_weight', parseFloat(e.target.value) || 0)}
                                  style={{ width: '80px', padding: '0.4rem 0.5rem', border: '1px solid #ddd', borderRadius: '6px', textAlign: 'center', fontSize: '0.9rem' }}
                                />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}

                <div className="form-group">
                  <label htmlFor="cfg-start-date">Start Date</label>
                  <input
                    type="date"
                    id="cfg-start-date"
                    value={startDate}
                    onChange={e => setStartDate(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="cfg-notes">Notes for Client (optional)</label>
                  <textarea
                    id="cfg-notes"
                    value={notes}
                    onChange={e => setNotes(e.target.value)}
                    placeholder="Any notes or instructions..."
                    rows={2}
                  />
                </div>
              </>
            )}

            <div className="modal-footer">
              <button
                className="btn-secondary"
                onClick={() => setStep(initialTemplateId ? 'pick_client' : 'pick_template')}
                disabled={loadingParams}
              >
                Back
              </button>
              <button
                className="btn-primary"
                onClick={handleGenerate}
                disabled={loadingParams || movements.length === 0}
              >
                Generate Draft
              </button>
            </div>
          </div>
        )}

        {/* Step: generating */}
        {step === 'generating' && (
          <div className="modal-body">
            <div className="assign-loading" style={{ padding: '3rem' }}>
              <div className="spinner" />
              <p>Generating personalized program for {selectedClientName}...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
