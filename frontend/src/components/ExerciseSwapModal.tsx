import { useState, useEffect } from 'react';
import { getAlternatives, applyOverrides } from '../services/engineProxy';
import type { EngineBlock, GeneratedPlan, ExerciseAlternative } from '../types/engine';
import './ExerciseSwapModal.css';

interface Props {
  isOpen: boolean;
  block: EngineBlock;
  athleteEquipment: string[];
  currentPlan: GeneratedPlan;
  onApplySwap: (updatedPlan: GeneratedPlan) => void;
  onClose: () => void;
}

export default function ExerciseSwapModal({
  isOpen, block, athleteEquipment, currentPlan, onApplySwap, onClose,
}: Props) {
  const [alternatives, setAlternatives] = useState<ExerciseAlternative[]>([]);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    setError(null);
    getAlternatives({
      exercise_id: block.exercise.id,
      athlete_equipment: athleteEquipment,
      limit: 6,
    })
      .then(r => setAlternatives(r.alternatives))
      .catch(() => setError('Could not load alternatives'))
      .finally(() => setLoading(false));
  }, [isOpen, block.exercise.id]);

  async function handleSwap(alt: ExerciseAlternative) {
    setApplying(alt.id);
    setError(null);
    try {
      const result = await applyOverrides({
        plan: currentPlan,
        overrides: [{ block_id: block.block_id, new_exercise_id: alt.id }],
      });
      if (result.rejected && result.rejected.length > 0) {
        setError('Swap was rejected: incompatible exercise');
      } else {
        onApplySwap(result.plan);
        onClose();
      }
    } catch {
      setError('Failed to apply swap');
    } finally {
      setApplying(null);
    }
  }

  if (!isOpen) return null;

  return (
    <div className="swap-overlay" onClick={onClose}>
      <div className="swap-modal" onClick={e => e.stopPropagation()}>
        <div className="swap-header">
          <div>
            <h3>Swap Exercise</h3>
            <p className="swap-original">Replacing: <strong>{block.exercise.name}</strong></p>
          </div>
          <button className="swap-close" onClick={onClose}>×</button>
        </div>

        {error && <p className="swap-error">{error}</p>}

        {loading ? (
          <p className="swap-loading">Loading alternatives…</p>
        ) : alternatives.length === 0 ? (
          <p className="swap-empty">No alternatives found for your equipment.</p>
        ) : (
          <ul className="swap-list">
            {alternatives.map(alt => (
              <li key={alt.id} className="swap-item">
                <div className="swap-info">
                  <span className="swap-name">{alt.name}</span>
                  <span className={`swap-badge ${alt.match_reason === 'swap_group' ? 'badge-direct' : 'badge-similar'}`}>
                    {alt.match_reason === 'swap_group' ? 'Direct swap' : 'Similar'}
                  </span>
                </div>
                <button
                  className="swap-btn"
                  disabled={applying === alt.id}
                  onClick={() => handleSwap(alt)}
                >
                  {applying === alt.id ? '…' : 'Use this'}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
