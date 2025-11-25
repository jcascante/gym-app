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
import { getClientDetail } from '../services/clients';
import { assignProgramToClient } from '../services/programAssignments';

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
}

type Step = 'movements' | 'oneRM' | 'eightyPercentTest' | 'fiveRMTest' | 'program';

export default function ProgramBuilder() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const clientId = searchParams.get('clientId');

  const [currentStep, setCurrentStep] = useState<Step>('movements');
  const [movements, setMovements] = useState<Movement[]>([]);
  const [selectedMovement, setSelectedMovement] = useState<Movement | null>(null);
  const [newMovementName, setNewMovementName] = useState('');
  const [selectedWeek, setSelectedWeek] = useState<number | 'all'>(1);
  const [lastSingleWeek, setLastSingleWeek] = useState<number>(1);
  const [isSaving, setIsSaving] = useState(false);
  const [constantsLoaded, setConstantsLoaded] = useState(false);
  const [clientName, setClientName] = useState<string>('');
  const [loadingClient, setLoadingClient] = useState(false);

  // Fetch calculation constants from backend on mount
  useEffect(() => {
    fetchCalculationConstants()
      .then(() => {
        console.log('✅ Calculation constants loaded from backend');
        setConstantsLoaded(true);
      })
      .catch(err => {
        console.error('Failed to load constants:', err);
        // Will use fallback constants - app still works
        setConstantsLoaded(true);
      });
  }, []);

  // Load client details if building for a specific client
  useEffect(() => {
    if (clientId) {
      setLoadingClient(true);
      getClientDetail(clientId)
        .then(client => {
          const profile = client.profile || {};
          const basicInfo = profile.basic_info || {};
          const name = `${basicInfo.first_name || 'Unknown'} ${basicInfo.last_name || 'Client'}`;
          setClientName(name);
        })
        .catch(err => {
          console.error('Failed to load client details:', err);
        })
        .finally(() => {
          setLoadingClient(false);
        });
    }
  }, [clientId]);

  // Save program to backend
  const handleSaveProgram = async () => {
    setIsSaving(true);

    try {
      // Prepare input data for backend
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
          target_weight: m.targetWeight
        })),
        duration_weeks: 8,
        days_per_week: 4,
        is_template: !clientId  // If building for client, not a template
      };

      // Save program using apiFetch
      const savedProgram = await apiFetch<any>('/programs', {
        method: 'POST',
        body: JSON.stringify(programInputs)
      });

      console.log('✅ Program saved successfully:', savedProgram);

      // If building for a client, assign the program
      if (clientId && savedProgram.id) {
        try {
          const assignment = await assignProgramToClient(savedProgram.id, {
            client_id: clientId,
            assignment_name: undefined,  // Use program name
            start_date: new Date().toISOString().split('T')[0],  // Today
            notes: 'Program created and assigned via Program Builder'
          });

          console.log('✅ Program assigned to client:', assignment);
          alert(`Program created and assigned to ${clientName} successfully!`);

          // Navigate back to client detail page
          navigate(`/clients/${clientId}`);
        } catch (assignError) {
          console.error('Failed to assign program:', assignError);
          const errorMsg = assignError instanceof Error
            ? assignError.message
            : JSON.stringify(assignError);
          alert(`Program created but failed to assign to client: ${errorMsg}`);
        }
      } else {
        // Program saved as template
        alert(t('programBuilder.step5.saveSuccess'));
        // Could navigate to templates page
      }
    } catch (error) {
      console.error('❌ Failed to save program:', error);
      alert(t('programBuilder.step5.saveError', {
        error: error instanceof Error ? error.message : 'Unknown error'
      }));
    } finally {
      setIsSaving(false);
    }
  };

  const addMovement = (name: string) => {
    if (movements.length >= 4) {
      alert(t('programBuilder.step1.maxMovements'));
      return;
    }
    const newMovement: Movement = {
      id: Date.now().toString(),
      name,
      oneRM: 0,
      eightyPercentRM: 0,
      maxRepsAt80: 0,
      weeklyJumpPercent: 0,
      weeklyJumpLbs: 0,
      rampUpPercent: 0,
      rampUpBaseLbs: 0,
      targetWeight: 0
    };
    setMovements([...movements, newMovement]);
  };

  const removeMovement = (id: string) => {
    setMovements(movements.filter(m => m.id !== id));
  };

  const updateMovement = (id: string, updates: Partial<Movement>) => {
    setMovements(movements.map(m => m.id === id ? { ...m, ...updates } : m));
  };

  const renderStepIndicator = () => {
    const steps = [
      { key: 'movements', label: t('programBuilder.steps.movements') },
      { key: 'oneRM', label: t('programBuilder.steps.oneRM') },
      { key: 'eightyPercentTest', label: t('programBuilder.steps.eightyPercent') },
      { key: 'fiveRMTest', label: t('programBuilder.steps.fiveRM') },
      { key: 'program', label: t('programBuilder.steps.program') }
    ];

    return (
      <div className="step-indicator">
        {steps.map((step, index) => (
          <div
            key={step.key}
            className={`step ${currentStep === step.key ? 'active' : ''}`}
          >
            <div className="step-number">{index + 1}</div>
            <div className="step-label">{step.label}</div>
          </div>
        ))}
      </div>
    );
  };

  const renderMovementsStep = () => {
    return (
      <div className="step-content">
        <h2>{t('programBuilder.step1.title')}</h2>
        <p className="step-description">
          {t('programBuilder.step1.description')}
        </p>

        <div className="movement-input">
          <input
            type="text"
            placeholder={t('programBuilder.step1.placeholder')}
            value={newMovementName}
            onChange={(e) => setNewMovementName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && newMovementName.trim()) {
                addMovement(newMovementName.trim());
                setNewMovementName('');
              }
            }}
          />
          <button
            onClick={() => {
              if (newMovementName.trim()) {
                addMovement(newMovementName.trim());
                setNewMovementName('');
              }
            }}
            disabled={movements.length >= 4}
          >
            {t('programBuilder.step1.addButton')}
          </button>
        </div>

        <div className="movements-list">
          {movements.map((movement) => (
            <div key={movement.id} className="movement-card">
              <span>{movement.name}</span>
              <button
                className="remove-btn"
                onClick={() => removeMovement(movement.id)}
              >
                ✕
              </button>
            </div>
          ))}
        </div>

        <div className="step-actions">
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
  };

  const renderOneRMStep = () => {
    const completedTests = movements.filter(m => m.oneRM > 0).length;
    const totalTests = movements.length;

    return (
      <div className="step-content">
        <div className="step-header-with-progress">
          <div>
            <h2>{t('programBuilder.step2.title')}</h2>
            <p className="step-description">
              {t('programBuilder.step2.description')}
            </p>
          </div>
          <div className="progress-badge">
            <span className="progress-count">{completedTests}/{totalTests}</span>
            <span className="progress-label">{t('programBuilder.step2.completed')}</span>
          </div>
        </div>

        {/* Instructions Section */}
        <div className="instructions-box">
          <div className="instruction-header">
            <span className="instruction-icon">📋</span>
            <h3>{t('programBuilder.step2.whatIs1RM')}</h3>
          </div>
          <p>
            {t('programBuilder.step2.oneRMDefinition')}
          </p>

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

        {/* Test Inputs */}
        <div className="test-section">
          <h3 className="section-title">{t('programBuilder.step2.enterResults')}</h3>
          <div className="movements-grid">
            {movements.map((movement, index) => (
              <div
                key={movement.id}
                className={`movement-test-card ${movement.oneRM > 0 ? 'completed' : ''}`}
              >
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
                      onChange={(e) => {
                        const value = e.target.value === '' ? 0 : Number(e.target.value);
                        const eightyPercent = calculate80Percent(value);
                        updateMovement(movement.id, {
                          oneRM: value,
                          eightyPercentRM: eightyPercent
                        });
                      }}
                      placeholder={t('programBuilder.step2.placeholder')}
                      min="0"
                      step="5"
                    />
                    <span className="unit-label">lbs</span>
                  </div>
                </div>

                {movement.oneRM > 0 && (
                  <div className="calculation-result">
                    <div className="result-row">
                      <span className="result-label">{t('programBuilder.step2.eightyPercentOf1RM')}</span>
                      <strong className="result-value">{movement.eightyPercentRM} lbs</strong>
                    </div>
                    <p className="result-note">
                      {t('programBuilder.step2.nextTestNote')}
                    </p>
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

        {/* Progress Summary */}
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
                <span>
                  {t('programBuilder.step2.progress', { completed: completedTests, total: totalTests })}
                </span>
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

  const renderEightyPercentStep = () => {
    return (
      <div className="step-content">
        <h2>{t('programBuilder.step3.title')}</h2>
        <p className="step-description">
          {t('programBuilder.step3.description')}
        </p>

        <div className="movements-grid">
          {movements.map((movement) => (
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
                  onChange={async (e) => {
                    const value = e.target.value === '' ? 0 : Number(e.target.value);

                    // Calculate jump and ramp up using backend constants
                    if (value > 0 && value <= 20) {
                      // Use backend calculation service
                      const jumpData = await calculateWeeklyJump(value, movement.oneRM);
                      const rampUpData = await calculateRampUp(value, movement.oneRM);

                      updateMovement(movement.id, {
                        maxRepsAt80: value,
                        weeklyJumpPercent: jumpData.percent,
                        weeklyJumpLbs: jumpData.lbs,
                        rampUpPercent: rampUpData.percent,
                        rampUpBaseLbs: rampUpData.baseLbs
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
  };

  const renderFiveRMTest = () => {
    return (
      <div className="step-content">
        <h2>{t('programBuilder.step4.title')}</h2>
        <p className="step-description">
          {t('programBuilder.step4.description')}
        </p>

        <div className="movements-selection">
          {movements.map((movement) => (
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
                  onChange={(e) => {
                    const value = e.target.value === '' ? 0 : Number(e.target.value);
                    updateMovement(selectedMovement.id, { targetWeight: value });
                    // Update selectedMovement to keep it in sync
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
  };

  const renderWeekTabs = () => {
    const handleWeekClick = (week: number) => {
      setLastSingleWeek(week);
      setSelectedWeek(week);
    };

    const handleViewAllToggle = () => {
      if (selectedWeek === 'all') {
        // Go back to the last single week viewed
        setSelectedWeek(lastSingleWeek);
      } else {
        // Save current week and switch to all
        setLastSingleWeek(selectedWeek as number);
        setSelectedWeek('all');
      }
    };

    return (
      <div className="week-tabs-container">
        <div className="week-tabs">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((week) => (
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
            {selectedWeek === 'all'
              ? `← ${t('programBuilder.step5.week')} ${lastSingleWeek}`
              : 'View All'}
          </button>
        </div>
      </div>
    );
  };

  const renderProgramStep = () => {
    // Helper to calculate light day weight (80% of heavy day)
    const getLightWeight = (heavyWeight: number) => Math.round(heavyWeight * 0.8);

    return (
      <div className="step-content">
        <h2>{t('programBuilder.step5.title')}</h2>
        <p className="step-description">
          {t('programBuilder.step5.description')}
        </p>

        {renderWeekTabs()}

        <div className="program-info-box">
          <h3>Session Structure</h3>
          <p>Each exercise is performed 4 times per week, alternating between <strong>HEAVY</strong> (uppercase) and <strong>LIGHT</strong> (lowercase) days</p>
          <ul>
            <li><strong>Session 1:</strong> All exercises HEAVY</li>
            <li><strong>Session 2:</strong> All exercises light (80% of heavy weight)</li>
            <li><strong>Session 3:</strong> All exercises HEAVY</li>
            <li><strong>Session 4:</strong> All exercises light (80% of heavy weight)</li>
          </ul>
          <p className="note">Pattern for each exercise: HEAVY - light - HEAVY - light</p>
        </div>

        {/* Movement Summaries */}
        <div className="movements-summary">
          <h3>{t('programBuilder.step5.programSummary')}</h3>
          {movements.map((movement) => (
            <div key={movement.id} className="program-card">
              <h4>{movement.name}</h4>
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
            </div>
          ))}
        </div>

        {/* Quick Reference Table */}
        <div className="quick-reference">
          <h3>8-Week Progression Overview</h3>
          <div className="reference-table-container">
            <table className="reference-table">
              <thead>
                <tr>
                  <th>Movement</th>
                  <th>{t('programBuilder.step5.week')} 1</th>
                  <th>{t('programBuilder.step5.week')} 2</th>
                  <th>{t('programBuilder.step5.week')} 3</th>
                  <th>{t('programBuilder.step5.week')} 4</th>
                  <th>{t('programBuilder.step5.week')} 5</th>
                  <th>{t('programBuilder.step5.week')} 6</th>
                  <th>{t('programBuilder.step5.week')} 7</th>
                  <th>{t('programBuilder.step5.week')} 8</th>
                </tr>
              </thead>
              <tbody>
                {movements.map((movement) => {
                  const weights = [
                    movement.targetWeight - (4 * movement.weeklyJumpLbs), // Week 1
                    movement.targetWeight - (3 * movement.weeklyJumpLbs), // Week 2
                    movement.targetWeight - (2 * movement.weeklyJumpLbs), // Week 3
                    movement.targetWeight - movement.weeklyJumpLbs,       // Week 4
                    movement.targetWeight,                                 // Week 5
                    movement.targetWeight + movement.weeklyJumpLbs,       // Week 6
                    movement.targetWeight + (2 * movement.weeklyJumpLbs), // Week 7
                  ];
                  return (
                    <tr key={movement.id}>
                      <td className="movement-name-cell">{movement.name}</td>
                      <td className="weight-cell">{weights[0]} lbs</td>
                      <td className="weight-cell">{weights[1]} lbs</td>
                      <td className="weight-cell">{weights[2]} lbs</td>
                      <td className="weight-cell">{weights[3]} lbs</td>
                      <td className="weight-cell highlight-cell">{weights[4]} lbs</td>
                      <td className="weight-cell">{weights[5]} lbs</td>
                      <td className="weight-cell">{weights[6]} lbs</td>
                      <td className="test-cell">{t('programBuilder.step5.test1RM')}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="reference-note">
            <strong>Note:</strong> Weeks 1-5 use 5x5 protocol, Week 6 uses 3x3, Week 7 uses 2x2, Week 8 is testing week
          </p>
        </div>

        {/* Weekly Program by Sessions */}
        <div className="sessions-program">
          <h3>Weekly Training Schedule</h3>

          {/* Weeks 1-5 with 5x5 */}
          {[1, 2, 3, 4, 5].filter(week => selectedWeek === 'all' || selectedWeek === week).map((week) => (
            <div key={week} className="week-block">
              <h4>{t('programBuilder.step5.week')} {week}</h4>
              <div className="sessions-grid">
                {/* Session 1 - All Heavy */}
                <div className="session-card">
                  <div className="session-header">
                    <span className="session-title">Session 1 - Heavy Day</span>
                    <span className="session-day">Monday</span>
                  </div>
                  <div className="session-exercises">
                    {movements.map((movement) => {
                      const heavyWeight = movement.targetWeight - ((5 - week) * movement.weeklyJumpLbs);
                      const percentage = Math.round((heavyWeight / movement.oneRM) * 100);
                      return (
                        <div key={movement.id} className="exercise heavy-exercise">
                          <span className="exercise-name">{movement.name.toUpperCase()}</span>
                          <span className="exercise-protocol">5x5</span>
                          <span className="exercise-weight">{heavyWeight} lbs <span className="percentage">({percentage}%)</span></span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Session 2 - All Light */}
                <div className="session-card">
                  <div className="session-header">
                    <span className="session-title">Session 2 - Light Day</span>
                    <span className="session-day">Wednesday</span>
                  </div>
                  <div className="session-exercises">
                    {movements.map((movement) => {
                      const heavyWeight = movement.targetWeight - ((5 - week) * movement.weeklyJumpLbs);
                      const lightWeight = getLightWeight(heavyWeight);
                      const percentage = Math.round((lightWeight / movement.oneRM) * 100);
                      return (
                        <div key={movement.id} className="exercise light-exercise">
                          <span className="exercise-name">{movement.name.toLowerCase()}</span>
                          <span className="exercise-protocol">5x5</span>
                          <span className="exercise-weight">{lightWeight} lbs <span className="percentage">({percentage}%)</span></span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Session 3 - All Heavy */}
                <div className="session-card">
                  <div className="session-header">
                    <span className="session-title">Session 3 - Heavy Day</span>
                    <span className="session-day">Friday</span>
                  </div>
                  <div className="session-exercises">
                    {movements.map((movement) => {
                      const heavyWeight = movement.targetWeight - ((5 - week) * movement.weeklyJumpLbs);
                      const percentage = Math.round((heavyWeight / movement.oneRM) * 100);
                      return (
                        <div key={movement.id} className="exercise heavy-exercise">
                          <span className="exercise-name">{movement.name.toUpperCase()}</span>
                          <span className="exercise-protocol">5x5</span>
                          <span className="exercise-weight">{heavyWeight} lbs <span className="percentage">({percentage}%)</span></span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Session 4 - All Light */}
                <div className="session-card">
                  <div className="session-header">
                    <span className="session-title">Session 4 - Light Day</span>
                    <span className="session-day">Saturday</span>
                  </div>
                  <div className="session-exercises">
                    {movements.map((movement) => {
                      const heavyWeight = movement.targetWeight - ((5 - week) * movement.weeklyJumpLbs);
                      const lightWeight = getLightWeight(heavyWeight);
                      const percentage = Math.round((lightWeight / movement.oneRM) * 100);
                      return (
                        <div key={movement.id} className="exercise light-exercise">
                          <span className="exercise-name">{movement.name.toLowerCase()}</span>
                          <span className="exercise-protocol">5x5</span>
                          <span className="exercise-weight">{lightWeight} lbs <span className="percentage">({percentage}%)</span></span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {/* Week 6 - 3x3 */}
          {(selectedWeek === 'all' || selectedWeek === 6) && (
          <div className="week-block">
            <h4>{t('programBuilder.step5.week')} 6</h4>
            <div className="sessions-grid">
              {/* Session 1 - All Heavy */}
              <div className="session-card">
                <div className="session-header">
                  <span className="session-title">Session 1 - Heavy Day</span>
                  <span className="session-day">Monday</span>
                </div>
                <div className="session-exercises">
                  {movements.map((movement) => {
                    const heavyWeight = movement.targetWeight + movement.weeklyJumpLbs;
                    const percentage = Math.round((heavyWeight / movement.oneRM) * 100);
                    return (
                      <div key={movement.id} className="exercise heavy-exercise">
                        <span className="exercise-name">{movement.name.toUpperCase()}</span>
                        <span className="exercise-protocol">3x3</span>
                        <span className="exercise-weight">{heavyWeight} lbs <span className="percentage">({percentage}%)</span></span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Session 2 - All Light */}
              <div className="session-card">
                <div className="session-header">
                  <span className="session-title">Session 2 - Light Day</span>
                  <span className="session-day">Wednesday</span>
                </div>
                <div className="session-exercises">
                  {movements.map((movement) => {
                    const heavyWeight = movement.targetWeight + movement.weeklyJumpLbs;
                    const lightWeight = getLightWeight(heavyWeight);
                    const percentage = Math.round((lightWeight / movement.oneRM) * 100);
                    return (
                      <div key={movement.id} className="exercise light-exercise">
                        <span className="exercise-name">{movement.name.toLowerCase()}</span>
                        <span className="exercise-protocol">3x3</span>
                        <span className="exercise-weight">{lightWeight} lbs <span className="percentage">({percentage}%)</span></span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Session 3 - All Heavy */}
              <div className="session-card">
                <div className="session-header">
                  <span className="session-title">Session 3 - Heavy Day</span>
                  <span className="session-day">Friday</span>
                </div>
                <div className="session-exercises">
                  {movements.map((movement) => {
                    const heavyWeight = movement.targetWeight + movement.weeklyJumpLbs;
                    const percentage = Math.round((heavyWeight / movement.oneRM) * 100);
                    return (
                      <div key={movement.id} className="exercise heavy-exercise">
                        <span className="exercise-name">{movement.name.toUpperCase()}</span>
                        <span className="exercise-protocol">3x3</span>
                        <span className="exercise-weight">{heavyWeight} lbs <span className="percentage">({percentage}%)</span></span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Session 4 - All Light */}
              <div className="session-card">
                <div className="session-header">
                  <span className="session-title">Session 4 - Light Day</span>
                  <span className="session-day">Saturday</span>
                </div>
                <div className="session-exercises">
                  {movements.map((movement) => {
                    const heavyWeight = movement.targetWeight + movement.weeklyJumpLbs;
                    const lightWeight = getLightWeight(heavyWeight);
                    const percentage = Math.round((lightWeight / movement.oneRM) * 100);
                    return (
                      <div key={movement.id} className="exercise light-exercise">
                        <span className="exercise-name">{movement.name.toLowerCase()}</span>
                        <span className="exercise-protocol">3x3</span>
                        <span className="exercise-weight">{lightWeight} lbs <span className="percentage">({percentage}%)</span></span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
          )}

          {/* Week 7 - 2x2 */}
          {(selectedWeek === 'all' || selectedWeek === 7) && (
          <div className="week-block">
            <h4>{t('programBuilder.step5.week')} 7</h4>
            <div className="sessions-grid">
              {/* Session 1 - All Heavy */}
              <div className="session-card">
                <div className="session-header">
                  <span className="session-title">Session 1 - Heavy Day</span>
                  <span className="session-day">Monday</span>
                </div>
                <div className="session-exercises">
                  {movements.map((movement) => {
                    const heavyWeight = movement.targetWeight + (movement.weeklyJumpLbs * 2);
                    const percentage = Math.round((heavyWeight / movement.oneRM) * 100);
                    return (
                      <div key={movement.id} className="exercise heavy-exercise">
                        <span className="exercise-name">{movement.name.toUpperCase()}</span>
                        <span className="exercise-protocol">2x2</span>
                        <span className="exercise-weight">{heavyWeight} lbs <span className="percentage">({percentage}%)</span></span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Session 2 - All Light */}
              <div className="session-card">
                <div className="session-header">
                  <span className="session-title">Session 2 - Light Day</span>
                  <span className="session-day">Wednesday</span>
                </div>
                <div className="session-exercises">
                  {movements.map((movement) => {
                    const heavyWeight = movement.targetWeight + (movement.weeklyJumpLbs * 2);
                    const lightWeight = getLightWeight(heavyWeight);
                    const percentage = Math.round((lightWeight / movement.oneRM) * 100);
                    return (
                      <div key={movement.id} className="exercise light-exercise">
                        <span className="exercise-name">{movement.name.toLowerCase()}</span>
                        <span className="exercise-protocol">2x2</span>
                        <span className="exercise-weight">{lightWeight} lbs <span className="percentage">({percentage}%)</span></span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Session 3 - All Heavy */}
              <div className="session-card">
                <div className="session-header">
                  <span className="session-title">Session 3 - Heavy Day</span>
                  <span className="session-day">Friday</span>
                </div>
                <div className="session-exercises">
                  {movements.map((movement) => {
                    const heavyWeight = movement.targetWeight + (movement.weeklyJumpLbs * 2);
                    const percentage = Math.round((heavyWeight / movement.oneRM) * 100);
                    return (
                      <div key={movement.id} className="exercise heavy-exercise">
                        <span className="exercise-name">{movement.name.toUpperCase()}</span>
                        <span className="exercise-protocol">2x2</span>
                        <span className="exercise-weight">{heavyWeight} lbs <span className="percentage">({percentage}%)</span></span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Session 4 - All Light */}
              <div className="session-card">
                <div className="session-header">
                  <span className="session-title">Session 4 - Light Day</span>
                  <span className="session-day">Saturday</span>
                </div>
                <div className="session-exercises">
                  {movements.map((movement) => {
                    const heavyWeight = movement.targetWeight + (movement.weeklyJumpLbs * 2);
                    const lightWeight = getLightWeight(heavyWeight);
                    const percentage = Math.round((lightWeight / movement.oneRM) * 100);
                    return (
                      <div key={movement.id} className="exercise light-exercise">
                        <span className="exercise-name">{movement.name.toLowerCase()}</span>
                        <span className="exercise-protocol">2x2</span>
                        <span className="exercise-weight">{lightWeight} lbs <span className="percentage">({percentage}%)</span></span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
          )}

          {/* Week 8 - Test Week */}
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
                  {movements.map((movement) => (
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
                  <li><strong>Rest 2-3 days</strong> before your test day to ensure full recovery</li>
                  <li><strong>Test 1RM</strong> for all movements using proper warm-up protocol</li>
                  <li><strong>Rest for the remainder</strong> of the week after testing</li>
                  <li>Record your new 1RM values to track progress</li>
                </ul>
                <p className="test-week-note">
                  <strong>Note:</strong> This is a deload and testing week. Focus on recovery and establishing new personal records safely.
                </p>
              </div>
            </div>
          </div>
          )}
        </div>

        <div className="step-actions">
          <button className="secondary-btn" onClick={() => setCurrentStep('fiveRMTest')}>
            {t('programBuilder.step5.backButton')}
          </button>
          <button
            className="primary-btn"
            onClick={handleSaveProgram}
            disabled={isSaving}
          >
            {isSaving ? t('programBuilder.step5.saving') : t('programBuilder.step5.saveButton')}
          </button>
        </div>
      </div>
    );
  };

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 'movements':
        return renderMovementsStep();
      case 'oneRM':
        return renderOneRMStep();
      case 'eightyPercentTest':
        return renderEightyPercentStep();
      case 'fiveRMTest':
        return renderFiveRMTest();
      case 'program':
        return renderProgramStep();
      default:
        return renderMovementsStep();
    }
  };

  return (
    <div className="program-builder">
      <div className="builder-header">
        <h1>{t('programBuilder.title')}</h1>
        <p>{t('programBuilder.subtitle')}</p>
        {clientId && clientName && (
          <div className="client-indicator">
            <span className="client-label">Building for:</span>
            <span className="client-name">{clientName}</span>
            <button
              className="btn-link"
              onClick={() => navigate(`/clients/${clientId}`)}
              style={{ marginLeft: '1rem' }}
            >
              View Client →
            </button>
          </div>
        )}
        {clientId && loadingClient && (
          <div className="client-indicator">
            <span className="client-label">Loading client...</span>
          </div>
        )}
      </div>

      {renderStepIndicator()}
      {renderCurrentStep()}
    </div>
  );
}
