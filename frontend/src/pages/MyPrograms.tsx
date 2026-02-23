import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMyPrograms } from '../services/programAssignments';
import type { ProgramAssignmentSummary } from '../services/programAssignments';
import './Programs.css';

export default function MyPrograms() {
  const [programs, setPrograms] = useState<ProgramAssignmentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const res = await getMyPrograms();
        setPrograms(res.programs || []);
      } catch (err) {
        console.error('Failed to load my programs', err);
        setError('Failed to load programs');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const navigate = useNavigate();

  return (
    <div className="programs-page">
      <div className="programs-header">
        <h1>My Programs</h1>
        <p>Programs assigned to you</p>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : error ? (
        <p style={{ color: 'red' }}>{error}</p>
      ) : programs.length === 0 ? (
        <p>No program assignments yet.</p>
      ) : (
        <div className="programs-grid">
          {programs.map((p) => (
            <div
              key={p.assignment_id}
              className="program-card"
              role="button"
              onClick={() => navigate(`/my-programs/${p.assignment_id}`)}
              style={{ cursor: 'pointer' }}
            >
              <h3>{p.program_name}</h3>
              <p style={{ color: '#666' }}>{p.assignment_name}</p>
              <div className="program-meta">
                <span>{p.duration_weeks}w</span>
                <span>{p.days_per_week}d/w</span>
                <span>{Math.round(p.progress_percentage)}%</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
