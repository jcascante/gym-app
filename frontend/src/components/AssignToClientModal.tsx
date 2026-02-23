import { useState, useEffect } from 'react';
import { listMyClients, type ClientSummary } from '../services/clients';
import { assignProgramToClient } from '../services/programAssignments';
import { ApiError } from '../services/api';
import './AssignProgramModal.css';

interface AssignToClientModalProps {
  programId: string;
  programName: string;
  onClose: () => void;
  onAssigned: () => void;
}

type Step = 'select' | 'confirm' | 'result';

export default function AssignToClientModal({
  programId,
  programName,
  onClose,
  onAssigned,
}: AssignToClientModalProps) {
  const [step, setStep] = useState<Step>('select');
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<ClientSummary | null>(null);
  const [startDate, setStartDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [resultMessage, setResultMessage] = useState('');
  const [resultSuccess, setResultSuccess] = useState(false);

  useEffect(() => {
    listMyClients()
      .then(res => setClients(res.clients))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleAssign = async () => {
    if (!selected) return;
    try {
      setSubmitting(true);
      await assignProgramToClient(programId, {
        client_id: selected.id,
        start_date: startDate,
        notes: notes.trim() || undefined,
      });
      setResultSuccess(true);
      setResultMessage(`"${programName}" has been assigned to ${selected.name}.`);
      setStep('result');
    } catch (err) {
      setResultSuccess(false);
      setResultMessage(err instanceof ApiError ? err.message : 'Failed to assign program. Please try again.');
      setStep('result');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDone = () => {
    if (resultSuccess) onAssigned();
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content assign-modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Assign "{programName}"</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {step === 'select' && (
          <div className="modal-body">
            <p className="form-hint">Select a client to assign this program to.</p>

            {loading ? (
              <div className="assign-loading">
                <div className="spinner" />
                <p>Loading clients...</p>
              </div>
            ) : clients.length === 0 ? (
              <div className="assign-empty">
                <p>No clients assigned to you yet.</p>
              </div>
            ) : (
              <div className="assign-program-list">
                {clients.map(client => (
                  <button
                    key={client.id}
                    className="assign-program-item"
                    onClick={() => { setSelected(client); setStep('confirm'); }}
                  >
                    <div className="assign-program-info">
                      <span className="assign-program-name">{client.name}</span>
                      <span className="assign-program-meta">
                        {client.active_programs} active program{client.active_programs !== 1 ? 's' : ''}
                        {' · '}{client.status}
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

        {step === 'confirm' && selected && (
          <div className="modal-body">
            <div className="confirm-program-banner">
              <span className="confirm-label">Assigning to</span>
              <strong>{selected.name}</strong>
              <span className="confirm-meta">{selected.active_programs} active program{selected.active_programs !== 1 ? 's' : ''}</span>
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
                placeholder="Add any notes or instructions..."
                rows={3}
              />
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setStep('select')}>Back</button>
              <button className="btn-primary" onClick={handleAssign} disabled={submitting}>
                {submitting ? 'Assigning...' : 'Assign Program'}
              </button>
            </div>
          </div>
        )}

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
