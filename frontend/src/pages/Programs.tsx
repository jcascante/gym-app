import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { listPrograms, deleteProgram, type ProgramSummary } from '../services/programs';
import { ApiError } from '../services/api';
import './Programs.css';

export default function Programs() {
  const navigate = useNavigate();
  const [programs, setPrograms] = useState<ProgramSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    loadPrograms();
  }, []);

  const loadPrograms = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await listPrograms({ is_template: false });
      setPrograms(res.programs);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to load programs');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (program: ProgramSummary) => {
    const isDraft = program.status === 'draft';
    const confirmed = window.confirm(
      isDraft
        ? `Discard draft "${program.name}"?\n\nThe program and its assignment will be permanently removed.`
        : `Delete "${program.name}"?\n\nThe program will be removed and any active client assignments will be cancelled. This cannot be undone.`
    );
    if (!confirmed) return;

    try {
      setDeletingId(program.id);
      await deleteProgram(program.id);
      setPrograms(prev => prev.filter(p => p.id !== program.id));
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Failed to delete program. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const filteredPrograms = useMemo(() => {
    if (!searchQuery.trim()) return programs;
    const q = searchQuery.toLowerCase();
    return programs.filter(p => p.name.toLowerCase().includes(q));
  }, [programs, searchQuery]);

  const formatDate = (isoStr: string) =>
    new Date(isoStr).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });

  const getViewPath = (program: ProgramSummary) => {
    if (program.status === 'draft') return `/programs/draft/${program.id}`;
    return `/programs/${program.id}`;
  };

  if (loading) {
    return (
      <div className="programs-page">
        <div className="loading-state">
          <div className="spinner" />
          <p>Loading programs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="programs-page">
      <div className="programs-header">
        <div className="header-text">
          <h1>Programs</h1>
          <p>{programs.length} program{programs.length !== 1 ? 's' : ''}</p>
        </div>
        <button className="btn-primary" onClick={() => navigate('/program-builder')}>
          <span className="button-icon">+</span>
          Build New Program
        </button>
      </div>

      {error && (
        <div className="error-banner">
          <span className="error-icon">!</span>
          <span>{error}</span>
        </div>
      )}

      <div className="programs-controls">
        <input
          type="search"
          className="search-input"
          placeholder="Search programs..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />
      </div>

      {filteredPrograms.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          {programs.length === 0 ? (
            <>
              <h2>No programs yet</h2>
              <p>Build a program for a client to get started.</p>
              <button className="btn-primary" onClick={() => navigate('/program-builder')}>
                Build First Program
              </button>
            </>
          ) : (
            <p>No programs match "{searchQuery}".</p>
          )}
        </div>
      ) : (
        <div className="programs-grid">
          {filteredPrograms.map(program => {
            const isDraft = program.status === 'draft';
            const isPublished = program.status === 'published';
            return (
              <div key={program.id} className="program-card">
                <div className="program-card-header">
                  <h3 className="program-name">{program.name}</h3>
                  {isDraft && <span className="prog-status-badge prog-status-draft">Draft</span>}
                  {isPublished && <span className="prog-status-badge prog-status-published">Published</span>}
                </div>
                <div className="program-meta">
                  <div className="meta-item">
                    <span className="meta-icon">📅</span>
                    <span>{program.duration_weeks} weeks</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-icon">🏋️</span>
                    <span>{program.days_per_week} days/week</span>
                  </div>
                </div>
                <div className="program-card-footer">
                  <span className="program-date">Created {formatDate(program.created_at)}</span>
                  <div className="program-actions">
                    <button className="btn-secondary-sm" onClick={() => navigate(getViewPath(program))}>
                      {isDraft ? 'Review Draft' : 'View'}
                    </button>
                    <button
                      className="btn-danger-sm"
                      onClick={() => handleDelete(program)}
                      disabled={deletingId === program.id}
                    >
                      {deletingId === program.id ? '...' : isDraft ? 'Discard' : 'Delete'}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
