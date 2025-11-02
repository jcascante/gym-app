import { useState } from 'react';
import './ProgramBuilder.css';

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
  const [currentStep, setCurrentStep] = useState<Step>('movements');
  const [movements, setMovements] = useState<Movement[]>([]);
  const [selectedMovement, setSelectedMovement] = useState<Movement | null>(null);
  const [newMovementName, setNewMovementName] = useState('');

  // Reference tables for calculations
  const weeklyJumpTable: { [key: number]: number } = {
    20: 2, 19: 2, 18: 2, 17: 2, 16: 2,
    15: 3, 14: 3, 13: 3, 12: 3, 11: 3,
    10: 4, 9: 4, 8: 4, 7: 4, 6: 4,
    5: 5, 4: 5, 3: 5, 2: 5, 1: 5
  };

  const rampUpTable: { [key: number]: number } = {
    20: 70, 19: 69, 18: 68, 17: 67, 16: 66,
    15: 65, 14: 64, 13: 63, 12: 62, 11: 61,
    10: 60, 9: 59, 8: 58, 7: 57, 6: 56,
    5: 55, 4: 54, 3: 53, 2: 52, 1: 51
  };

  const addMovement = (name: string) => {
    if (movements.length >= 4) {
      alert('Maximum 4 movements allowed');
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

  const calculateEightyPercent = (movement: Movement) => {
    const eightyPercent = Math.round(movement.oneRM * 0.8);
    updateMovement(movement.id, { eightyPercentRM: eightyPercent });
  };

  const calculateJumpAndRampUp = (movement: Movement) => {
    const reps = movement.maxRepsAt80;
    const weeklyJumpPercent = weeklyJumpTable[reps] || 5;
    const weeklyJumpLbs = Math.round((movement.oneRM * weeklyJumpPercent) / 100);
    const rampUpPercent = rampUpTable[reps] || 55;
    const rampUpBaseLbs = Math.round((movement.oneRM * rampUpPercent) / 100);

    updateMovement(movement.id, {
      weeklyJumpPercent,
      weeklyJumpLbs,
      rampUpPercent,
      rampUpBaseLbs
    });
  };

  const renderStepIndicator = () => {
    const steps = [
      { key: 'movements', label: 'Movements' },
      { key: 'oneRM', label: 'Test 1RM' },
      { key: 'eightyPercentTest', label: 'Test 80%' },
      { key: 'fiveRMTest', label: 'Test 5RM' },
      { key: 'program', label: 'Program' }
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
        <h2>Step #1: Select Movements</h2>
        <p className="step-description">
          Select up to 4 movements for your training program
        </p>

        <div className="movement-input">
          <input
            type="text"
            placeholder="Movement name (e.g., Squat, Bench Press)"
            value={newMovementName}
            onChange={(e) => setNewMovementName(e.target.value)}
            onKeyPress={(e) => {
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
            Add
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
            Next: Test 1RM
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
            <h2>Step #1: 1RM Test</h2>
            <p className="step-description">
              Test the 1RM for all movements you want to include in the plan (Maximum 4 movements)
            </p>
          </div>
          <div className="progress-badge">
            <span className="progress-count">{completedTests}/{totalTests}</span>
            <span className="progress-label">Completed</span>
          </div>
        </div>

        {/* Instructions Section */}
        <div className="instructions-box">
          <div className="instruction-header">
            <span className="instruction-icon">📋</span>
            <h3>What is 1RM?</h3>
          </div>
          <p>
            The <strong>1RM (One Rep Max)</strong> is the maximum weight you can lift
            in a specific movement for a single repetition with perfect technique.
          </p>

          <div className="instruction-tips">
            <h4>Safety Tips:</h4>
            <ul>
              <li>Perform an adequate warm-up before each test</li>
              <li>Increase weight progressively to find your 1RM</li>
              <li>Maintain perfect technique at all times</li>
              <li>Use a spotter or assistant when necessary</li>
              <li>Rest 3-5 minutes between attempts</li>
              <li>When in doubt, be conservative</li>
            </ul>
          </div>

          <div className="instruction-example">
            <strong>Example progression to find 1RM:</strong>
            <div className="example-progression">
              <span>Warm-up → 135 lbs x 10</span>
              <span>→ 225 lbs x 5</span>
              <span>→ 315 lbs x 3</span>
              <span>→ 405 lbs x 1</span>
              <span>→ 450 lbs x 1 ✓ (1RM)</span>
            </div>
          </div>
        </div>

        {/* Test Inputs */}
        <div className="test-section">
          <h3 className="section-title">Enter your 1RM results</h3>
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
                  <label>{t('programBuilder.step2.maxWeightLifted')} Maximum weight lifted (1RM)</label>
                  <div className="input-with-unit">
                    <input
                      type="number"
                      value={movement.oneRM || ''}
                      onChange={(e) => {
                        const value = e.target.value === '' ? 0 : Number(e.target.value);
                        const eightyPercent = value > 0 ? Math.round(value * 0.8) : 0;
                        updateMovement(movement.id, {
                          oneRM: value,
                          eightyPercentRM: eightyPercent
                        });
                      }}
                      placeholder="450"
                      min="0"
                      step="5"
                    />
                    <span className="unit-label">lbs</span>
                  </div>
                </div>

                {movement.oneRM > 0 && (
                  <div className="calculation-result">
                    <div className="result-row">
                      <span className="result-label">80% of 1RM:</span>
                      <strong className="result-value">{movement.eightyPercentRM} lbs</strong>
                    </div>
                    <p className="result-note">
                      This weight will be used in the next test
                    </p>
                  </div>
                )}

                {movement.oneRM === 0 && (
                  <div className="pending-message">
                    <span className="pending-icon">⏳</span>
                    <span>Pending input</span>
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
                <span>All tests completed! You can continue to the next step.</span>
              </div>
            ) : (
              <div className="info-message">
                <span className="info-icon">ℹ️</span>
                <span>
                  You have completed {completedTests} of {totalTests} tests.
                  Enter the remaining values to continue.
                </span>
              </div>
            )}
          </div>
        )}

        <div className="step-actions">
          <button className="secondary-btn" onClick={() => setCurrentStep('movements')}>
            ← Back
          </button>
          <button
            className="primary-btn"
            onClick={() => setCurrentStep('eightyPercentTest')}
            disabled={movements.some(m => m.oneRM === 0)}
          >
            Next: Test 80% →
          </button>
        </div>
      </div>
    );
  };

  const renderEightyPercentStep = () => {
    return (
      <div className="step-content">
        <h2>Step #2: Test with 80% of 1RM</h2>
        <p className="step-description">
          After one week, perform maximum reps with 80% of your 1RM
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
                <label>Maximum reps performed</label>
                <input
                  type="number"
                  value={movement.maxRepsAt80 || ''}
                  onChange={(e) => {
                    const value = e.target.value === '' ? 0 : Number(e.target.value);

                    // Calculate jump and ramp up inline to avoid double updates
                    if (value > 0 && value <= 20) {
                      const weeklyJumpPercent = weeklyJumpTable[value] || 5;
                      const weeklyJumpLbs = Math.round((movement.oneRM * weeklyJumpPercent) / 100);
                      const rampUpPercent = rampUpTable[value] || 55;
                      const rampUpBaseLbs = Math.round((movement.oneRM * rampUpPercent) / 100);

                      updateMovement(movement.id, {
                        maxRepsAt80: value,
                        weeklyJumpPercent,
                        weeklyJumpLbs,
                        rampUpPercent,
                        rampUpBaseLbs
                      });
                    } else {
                      updateMovement(movement.id, { maxRepsAt80: value });
                    }
                  }}
                  placeholder="4"
                  min="1"
                  max="20"
                />
              </div>
              {movement.maxRepsAt80 > 0 && (
                <div className="calculations">
                  <div className="calc-item">
                    <span>Weekly Jump:</span>
                    <strong>{movement.weeklyJumpPercent}% ({movement.weeklyJumpLbs} lbs)</strong>
                  </div>
                  <div className="calc-item">
                    <span>Ramp Up Base:</span>
                    <strong>{movement.rampUpPercent}% ({movement.rampUpBaseLbs} lbs)</strong>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="step-actions">
          <button className="secondary-btn" onClick={() => setCurrentStep('oneRM')}>
            ← Back
          </button>
          <button
            className="primary-btn"
            onClick={() => setCurrentStep('fiveRMTest')}
            disabled={movements.some(m => m.maxRepsAt80 === 0)}
          >
            Next: Test 5RM →
          </button>
        </div>
      </div>
    );
  };

  const renderFiveRMTest = () => {
    return (
      <div className="step-content">
        <h2>Step #3: 5RM Test</h2>
        <p className="step-description">
          Select a movement to perform the progressive 5-rep test
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
            <h3>Test Protocol - {selectedMovement.name}</h3>

            <div className="test-info">
              <div className="info-card">
                <label>Base Weight (Ramp Up)</label>
                <strong>{selectedMovement.rampUpBaseLbs} lbs</strong>
              </div>
              <div className="info-card">
                <label>Increment per Set</label>
                <strong>{selectedMovement.weeklyJumpLbs} lbs</strong>
              </div>
            </div>

            <div className="test-instructions">
              <h4>Instructions:</h4>
              <ol>
                <li>Do 5 reps with the Base Ramp Up ({selectedMovement.rampUpBaseLbs} lbs)</li>
                <li>Rest at least 3 minutes</li>
                <li>Add {selectedMovement.weeklyJumpLbs} lbs</li>
                <li>Do 5 reps</li>
                <li>Repeat steps 2, 3 and 4 until unable to complete 5 reps with perfect technique</li>
              </ol>
              <p className="note">
                <strong>Note:</strong> The heaviest set of 5 reps is your 5x5 target in the program
              </p>
            </div>

            <div className="test-progression">
              <h4>Suggested Progression:</h4>
              <div className="progression-list">
                {Array.from({ length: 8 }, (_, i) => {
                  const weight = selectedMovement.rampUpBaseLbs + (i * selectedMovement.weeklyJumpLbs);
                  return (
                    <div key={i} className="progression-item">
                      <span className="set-number">Set {i + 1}</span>
                      <span className="weight">{weight} lbs x 5</span>
                      {i < 7 && <span className="rest">rest 3 min</span>}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="target-input">
              <label>5x5 target achieved (weight of last set completed with 5 reps):</label>
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
                  placeholder="395"
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
            ← Back
          </button>
          <button
            className="primary-btn"
            onClick={() => setCurrentStep('program')}
            disabled={movements.some(m => m.targetWeight === 0)}
          >
            Generate Program →
          </button>
        </div>
      </div>
    );
  };

  const renderProgramStep = () => {
    return (
      <div className="step-content">
        <h2>Generated Program</h2>
        <p className="step-description">
          8-week linear strength program
        </p>

        {movements.map((movement) => (
          <div key={movement.id} className="program-card">
            <h3>{movement.name}</h3>

            <div className="program-summary-detailed">
              <h4>Program Summary</h4>
              <div className="summary-grid">
                <div className="summary-detail-item">
                  <span className="summary-label">Available Weight Jump</span>
                  <span className="summary-value">5 lbs</span>
                </div>
                <div className="summary-detail-item">
                  <span className="summary-label">1RM</span>
                  <span className="summary-value">{movement.oneRM} lbs</span>
                </div>
                <div className="summary-detail-item">
                  <span className="summary-label">80% 1RM</span>
                  <span className="summary-value">{movement.eightyPercentRM} lbs</span>
                </div>
                <div className="summary-detail-item">
                  <span className="summary-label">RM @80% 1RM</span>
                  <span className="summary-value">{movement.maxRepsAt80} reps</span>
                </div>
                <div className="summary-detail-item">
                  <span className="summary-label">Weekly Jump</span>
                  <span className="summary-value">{movement.weeklyJumpPercent}% / {movement.weeklyJumpLbs} lbs</span>
                </div>
                <div className="summary-detail-item">
                  <span className="summary-label">Initial Ramp Up</span>
                  <span className="summary-value">{movement.rampUpPercent}% / {movement.rampUpBaseLbs} lbs</span>
                </div>
                <div className="summary-detail-item highlight">
                  <span className="summary-label">5x5 TARGET</span>
                  <span className="summary-value">{movement.targetWeight} lbs</span>
                </div>
              </div>
            </div>

            <div className="weekly-program">
              {[1, 2, 3, 4, 5].map((week) => {
                const weight = movement.targetWeight - ((5 - week) * movement.weeklyJumpLbs);
                return (
                  <div key={week} className="week-item">
                    <span className="week-label">Week {week}</span>
                    <span className="week-protocol">5x5</span>
                    <span className="week-weight">{weight} lbs</span>
                  </div>
                );
              })}
              <div className="week-item">
                <span className="week-label">Week 6</span>
                <span className="week-protocol">3x3</span>
                <span className="week-weight">{movement.targetWeight + movement.weeklyJumpLbs} lbs</span>
              </div>
              <div className="week-item">
                <span className="week-label">Week 7</span>
                <span className="week-protocol">2x2</span>
                <span className="week-weight">{movement.targetWeight + (movement.weeklyJumpLbs * 2)} lbs</span>
              </div>
              <div className="week-item test-week">
                <span className="week-label">Week 8</span>
                <span className="week-protocol">Test Week</span>
                <span className="week-weight">Test 1RM</span>
              </div>
            </div>
          </div>
        ))}

        <div className="step-actions">
          <button className="secondary-btn" onClick={() => setCurrentStep('fiveRMTest')}>
            ← Back
          </button>
          <button className="primary-btn" onClick={() => alert('Save program (coming soon)')}>
            Save Program
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
        <h1>Program Builder</h1>
        <p>Create your linear strength training program</p>
      </div>

      {renderStepIndicator()}
      {renderCurrentStep()}
    </div>
  );
}
