import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listTemplates } from '../services/templates';
import type { TemplateListItem } from '../services/templates';
import styles from './TemplateLibrary.module.css';

export function TemplateLibrary() {
  const [templates, setTemplates] = useState<TemplateListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sourceFilter, setSourceFilter] = useState<'engine' | 'coach' | ''>('');
  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await listTemplates(sourceFilter ? { source: sourceFilter } : {});
        setTemplates(res.templates);
      } catch {
        setError('Failed to load templates');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [sourceFilter]);

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Program Templates</h1>
        <p>Browse available programs and start one today</p>
      </div>

      <div className={styles.filters}>
        <button
          className={sourceFilter === '' ? styles.filterActive : styles.filterBtn}
          onClick={() => setSourceFilter('')}
        >
          All
        </button>
        <button
          className={sourceFilter === 'engine' ? styles.filterActive : styles.filterBtn}
          onClick={() => setSourceFilter('engine')}
        >
          AI-Generated
        </button>
        <button
          className={sourceFilter === 'coach' ? styles.filterActive : styles.filterBtn}
          onClick={() => setSourceFilter('coach')}
        >
          Coach Created
        </button>
      </div>

      {loading ? (
        <p>Loading templates...</p>
      ) : error ? (
        <p className={styles.error}>{error}</p>
      ) : templates.length === 0 ? (
        <p>No templates available.</p>
      ) : (
        <div className={styles.grid}>
          {templates.map((t) => (
            <div
              key={`${t.source}-${t.id}`}
              className={styles.card}
              role="button"
              tabIndex={0}
              onClick={() => navigate(`/templates/${t.source}/${t.id}`)}
              onKeyDown={(e) => e.key === 'Enter' && navigate(`/templates/${t.source}/${t.id}`)}
            >
              <div className={styles.cardBadge}>
                {t.source === 'engine' ? 'AI' : 'Coach'}
              </div>
              <h3 className={styles.cardTitle}>{t.name}</h3>
              {t.description && (
                <p className={styles.cardDesc}>{t.description}</p>
              )}
              <div className={styles.cardMeta}>
                <span>{t.duration_weeks}w</span>
                <span>{t.days_per_week}d/w</span>
                {t.difficulty_level && <span>{t.difficulty_level}</span>}
              </div>
              {t.tags.length > 0 && (
                <div className={styles.tags}>
                  {t.tags.slice(0, 3).map((tag) => (
                    <span key={tag} className={styles.tag}>{tag}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
