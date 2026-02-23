import { useState, useEffect, useMemo } from 'react';
import { listPrograms, type ProgramSummary } from '../services/programs';
import { assignProgramToClient } from '../services/programAssignments';
import { ApiError } from '../services/api';
import './AssignProgramModal.css';

interface AssignProgramModalProps {
  clientId: string;
  clientName: string;
  onClose: () => void;
  onAssigned: () => void;
}

type Step = 'select' | 'confirm' | 'result';

export default function AssignProgramModal({
  clientId,
  clientName,
  onClose,
  onAssigned,
}: AssignProgramModalProps) {
  const [step, setStep] = useState<Step>('select');
  const [programs, setPrograms] = useState<ProgramSummary[]>([]);
  const [loadingPrograms, setLoadingPrograms] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selected, setSelected] = useState<ProgramSummary | null>(null);
  const [startDate, setStartDate] = useState(() => {
    return new Date().toISOString().split('T')[0];
  });
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [resultMessage, setResultMessage] = useState('');
  const [resultSuccess, setResultSuccess] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await listPrograms({ is_template: true });
        setPrograms(res.programs);
      } catch {
        // show empty state with message
      } finally {
        setLoadingPrograms(false);
      }
    };
    load();
  }, []);

  const filtered = useMemo(() => {
    if (!searchQuery.trim()) return programs;
    const q = searchQuery.toLowerCase();
    return programs.filter(p =>
      p.name.toLowerCase().includes(q) ||
      (p.description || '').toLowerCase().includes(q)
    );
  }, [programs, searchQuery]);

  const handleSelect = (program: ProgramSummary) => {
    setSelected(program);
    setStep('confirm');
  };

  const handleAssign = async () => {
    if (!selected) return;
    try {
      setSubmitting(true);
      await assignProgramToClient(selected.id, {
        client_id: clientId,
        start_date: startDate,
        notes: notes.trim() || undefined,
      });
      setResultSuccess(true);
      setResultMessage(`"${selected.name}" has been assigned to ${clientName}.`);
      setStep('result');
    } catch (err) {
      setResultSuccess(false);
      if (err instanceof ApiError) {
        setResultMessage(err.message);
      } else {
        setResultMessage('Failed to assign program. Please try again.');
      }
      setStep('result');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDone = () => {
    if (resultSuccess) {
      onAssigned();
    }
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content assign-modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Assign Program to {clientName}</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {/* Step 1: Select a program */}
        {step === 'select' && (
          <div className="modal-body">
            <p className="form-hint">Select a program template to assign to this client.</p>

            <input
              type="search"
              className="assign-search-input"
              placeholder="Search programs..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              autoFocus
            />

            {loadingPrograms ? (
              <div className="assign-loading">
                <div className="spinner" />
                <p>Loading programs...</p>
              </div>
            ) : filtered.length === 0 ? (
              <div className="assign-empty">
                {programs.length === 0 ? (
                  <p>No programs found. Build a program first in the Programs Library.</p>
                ) : (
                  <p>No programs match "{searchQuery}".</p>
                )}
              </div>
            ) : (
              <div className="assign-program-list">
                {filtered.map(program => (
                  <button
                    key={program.id}
                    className="assign-program-item"
                    onClick={() => handleSelect(program)}
                  >
                    <div className="assign-program-info">
                      <span className="assign-program-name">{program.name}</span>
                      <span className="assign-program-meta">
                        {program.duration_weeks} wks · {program.days_per_week} days/wk
                        {program.times_assigned > 0 && ` · Assigned ${program.times_assigned}x`}
                      </span>
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

        {/* Step 2: Confirm */}
        {step === 'confirm' && selected && (
          <div className="modal-body">
            <div className="confirm-program-banner">
              <span className="confirm-label">Selected program</span>
              <strong>{selected.name}</strong>
              <span className="confirm-meta">
                {selected.duration_weeks} weeks · {selected.days_per_week} days/week
              </span>
            </div>

            <div className="form-group">
              <label htmlFor="start-date">Start Date</label>
              <input
                type="date"
                id="start-date"
                value={startDate}
                onChange={e => setStartDate(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="assign-notes">Notes for Client (optional)</label>
              <textarea
                id="assign-notes"
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder="Add any notes or instructions for the client..."
                rows={3}
              />
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setStep('select')}>
                Back
              </button>
              <button
                className="btn-primary"
                onClick={handleAssign}
                disabled={submitting}
              >
                {submitting ? 'Assigning...' : 'Assign Program'}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Result */}
        {step === 'result' && (
          <div className="modal-body">
            <div className={`result-state ${resultSuccess ? 'success' : 'error'}`}>
              <div className="result-icon">{resultSuccess ? '✅' : '⚠️'}</div>
              <h3>{resultSuccess ? 'Program Assigned!' : 'Error'}</h3>
              <p>{resultMessage}</p>
              <div className="modal-footer">
                <button className="btn-primary" onClick={handleDone}>Done</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
