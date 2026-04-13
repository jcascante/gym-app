import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getTemplateDetail, selfStartProgram } from '../services/templates';
import styles from './TemplateDetail.module.css';

export function TemplateDetail() {
  const { source, templateId } = useParams<{ source: string; templateId: string }>();
  const navigate = useNavigate();

  const [template, setTemplate] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startDate, setStartDate] = useState<string>(() => {
    const d = new Date();
    return d.toISOString().split('T')[0];
  });
  const [assignmentName, setAssignmentName] = useState('');
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  useEffect(() => {
    if (!source || !templateId) return;
    const load = async () => {
      try {
        setLoading(true);
        const data = await getTemplateDetail(source as 'engine' | 'coach', templateId);
        setTemplate(data as Record<string, unknown>);
      } catch {
        setError('Failed to load template');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [source, templateId]);

  const handleStart = async () => {
    if (!source || !templateId) return;
    try {
      setStarting(true);
      setStartError(null);
      const res = await selfStartProgram(templateId, {
        source: source as 'engine' | 'coach',
        start_date: startDate || undefined,
        assignment_name: assignmentName || undefined,
      });
      navigate(`/my-programs/${res.assignment_id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to start program';
      setStartError(msg);
    } finally {
      setStarting(false);
    }
  };

  if (loading) return <div className={styles.page}><p>Loading...</p></div>;
  if (error) return <div className={styles.page}><p className={styles.error}>{error}</p></div>;
  if (!template) return null;

  const name = String(template.name ?? '');
  const description = template.description ? String(template.description) : undefined;
  const durationWeeks = Number(template.duration_weeks ?? 0);
  const daysPerWeek = Number(template.days_per_week ?? 0);
  const weeks = Array.isArray(template.weeks) ? template.weeks : [];

  return (
    <div className={styles.page}>
      <button className={styles.back} onClick={() => navigate('/templates')}>
        ← Back to Templates
      </button>

      <div className={styles.header}>
        <div className={styles.badge}>{source === 'engine' ? 'AI-Generated' : 'Coach Created'}</div>
        <h1>{name}</h1>
        {description && <p className={styles.desc}>{description}</p>}
        <div className={styles.meta}>
          <span>{durationWeeks} weeks</span>
          <span>{daysPerWeek} days/week</span>
        </div>
      </div>

      {/* Program structure preview */}
      {weeks.length > 0 && (
        <div className={styles.structure}>
          <h2>Program Structure</h2>
          {(weeks as Array<Record<string, unknown>>).slice(0, 2).map((week) => (
            <div key={String(week.week_number)} className={styles.week}>
              <h3>Week {String(week.week_number)}: {String(week.name ?? '')}</h3>
              {Array.isArray(week.days) &&
                (week.days as Array<Record<string, unknown>>).map((day) => (
                  <div key={String(day.day_number)} className={styles.day}>
                    <strong>Day {String(day.day_number)}: {String(day.name ?? '')}</strong>
                    {Array.isArray(day.exercises) && (
                      <ul className={styles.exercises}>
                        {(day.exercises as Array<Record<string, unknown>>).map((ex, i) => (
                          <li key={i}>
                            {String(ex.exercise_name ?? '')} — {String(ex.sets ?? '')} × {String(ex.reps ?? ex.reps_target ?? '?')}
                            {ex.weight_lbs ? ` @ ${String(ex.weight_lbs)} lbs` : ''}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
            </div>
          ))}
          {weeks.length > 2 && (
            <p className={styles.moreWeeks}>+ {weeks.length - 2} more weeks</p>
          )}
        </div>
      )}

      {/* Start form */}
      <div className={styles.startForm}>
        <h2>Start This Program</h2>

        <label className={styles.label}>
          Assignment name (optional)
          <input
            type="text"
            className={styles.input}
            placeholder={name}
            value={assignmentName}
            onChange={(e) => setAssignmentName(e.target.value)}
          />
        </label>

        <label className={styles.label}>
          Start date
          <input
            type="date"
            className={styles.input}
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </label>

        {startError && <p className={styles.error}>{startError}</p>}

        <button
          className={styles.startBtn}
          onClick={handleStart}
          disabled={starting}
        >
          {starting ? 'Starting...' : 'Start Program'}
        </button>
      </div>
    </div>
  );
}
