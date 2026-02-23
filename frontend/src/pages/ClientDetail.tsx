import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getClientDetail, getClientWorkoutHistory, updateClientOneRepMax, type ClientDetailResponse, type OneRepMax, type ClientWorkoutEntry, type UpdateOneRepMaxRequest } from '../services/clients';
import { getClientPrograms, removeProgramAssignment, type ProgramAssignmentSummary } from '../services/programAssignments';
import { ApiError } from '../services/api';
import EditProfileModal, { type ProfileSection } from '../components/EditProfileModal';
import './ClientDetail.css';

type TabType = 'overview' | 'profile' | 'programs' | 'progress';

export default function ClientDetail() {
  const { clientId } = useParams<{ clientId: string }>();
  const navigate = useNavigate();
  const [client, setClient] = useState<ClientDetailResponse | null>(null);
  const [programs, setPrograms] = useState<ProgramAssignmentSummary[]>([]);
  const [programsLoading, setProgramsLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [showCancelledPrograms, setShowCancelledPrograms] = useState(false);
  const [editSection, setEditSection] = useState<ProfileSection | null>(null);
  const [progressWorkouts, setProgressWorkouts] = useState<ClientWorkoutEntry[]>([]);
  const [progressLoading, setProgressLoading] = useState(false);
  const [showOrmModal, setShowOrmModal] = useState(false);
  const [ormForm, setOrmForm] = useState<UpdateOneRepMaxRequest>({
    exercise_name: '',
    weight: 0,
    unit: 'lbs',
    tested_date: new Date().toISOString().split('T')[0],
    verified: false,
  });
  const [ormSaving, setOrmSaving] = useState(false);
  const [ormError, setOrmError] = useState<string | null>(null);

  useEffect(() => {
    if (clientId) {
      loadClient();
    }
  }, [clientId]);

  const loadClient = async () => {
    if (!clientId) return;

    try {
      setLoading(true);
      setError(null);
      const data = await getClientDetail(clientId);
      setClient(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load client details');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadPrograms = async () => {
    if (!clientId) return;
    try {
      setProgramsLoading(true);
      const data = await getClientPrograms(clientId);
      setPrograms(data.programs);
    } catch {
      // Don't set error state — programs tab shows empty state on failure
    } finally {
      setProgramsLoading(false);
    }
  };

  const handleDeleteProgram = async (assignmentId: string, programName: string) => {
    if (!clientId) return;

    if (!confirm(`Are you sure you want to remove "${programName}" from this client?`)) {
      return;
    }

    try {
      await removeProgramAssignment(clientId, assignmentId);
      // Reload programs after deletion
      await loadPrograms();
      // Reload client to update stats
      await loadClient();
    } catch (err) {
      alert(`Failed to remove program: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  // Load programs when Programs tab is selected
  useEffect(() => {
    if (activeTab === 'programs' && clientId) {
      loadPrograms();
    }
    if (activeTab === 'progress' && clientId) {
      loadProgressWorkouts();
    }
  }, [activeTab, clientId]);

  const loadProgressWorkouts = async () => {
    if (!clientId) return;
    setProgressLoading(true);
    try {
      const data = await getClientWorkoutHistory(clientId);
      setProgressWorkouts(data.workouts);
    } catch {
      // silently fail — progress tab shows empty state
    } finally {
      setProgressLoading(false);
    }
  };

  const openOrmModal = (exerciseName?: string, existing?: OneRepMax) => {
    setOrmError(null);
    setOrmForm({
      exercise_name: exerciseName || '',
      weight: existing?.weight || 0,
      unit: existing?.unit || 'lbs',
      tested_date: existing?.tested_date || new Date().toISOString().split('T')[0],
      verified: existing?.verified || false,
    });
    setShowOrmModal(true);
  };

  const handleOrmSave = async () => {
    if (!clientId || !ormForm.exercise_name.trim() || ormForm.weight <= 0) {
      setOrmError('Exercise name and a positive weight are required.');
      return;
    }
    setOrmSaving(true);
    setOrmError(null);
    try {
      await updateClientOneRepMax(clientId, ormForm);
      setShowOrmModal(false);
      await loadClient(); // Refresh client to get updated 1RMs
    } catch (err) {
      if (err instanceof ApiError) {
        setOrmError(err.message);
      } else {
        setOrmError('Failed to save. Please try again.');
      }
    } finally {
      setOrmSaving(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleDateString();
  };

  const formatLastActivity = (dateString?: string) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="client-detail-page">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading client details...</p>
        </div>
      </div>
    );
  }

  if (error || !client) {
    return (
      <div className="client-detail-page">
        <div className="error-state">
          <div className="error-icon">⚠️</div>
          <h2>Error Loading Client</h2>
          <p>{error || 'Client not found'}</p>
          <button className="btn-primary" onClick={() => navigate('/clients')}>
            ← Back to Clients
          </button>
        </div>
      </div>
    );
  }

  const profile = client.profile || {};
  const basicInfo = profile.basic_info || {} as any;
  const anthropometrics = profile.anthropometrics || {} as any;
  const trainingExp = profile.training_experience || {} as any;
  const fitnessGoals = profile.fitness_goals || {} as any;
  const healthInfo = profile.health_info || {} as any;
  const trainingPrefs = profile.training_preferences || {} as any;
  const oneRepMaxes = trainingExp.one_rep_maxes || {};

  return (
    <div className="client-detail-page">
      {/* Header */}
      <div className="client-header">
        <button className="back-button" onClick={() => navigate('/clients')}>
          ← Back to Clients
        </button>

        <div className="client-header-content">
          <div className="client-header-left">
            <div className="client-avatar-large">
              {basicInfo.first_name?.[0] || 'C'}
              {basicInfo.last_name?.[0] || 'L'}
            </div>
            <div className="client-header-info">
              <h1>
                {basicInfo.first_name || 'Unknown'} {basicInfo.last_name || 'Client'}
              </h1>
              <p className="client-email">{client.email}</p>
              <div className="client-meta">
                <span className="meta-item">
                  📅 Client since {formatDate(client.assigned_at)}
                </span>
                <span className="meta-item">
                  🏋️ Last workout: {formatLastActivity(client.last_workout)}
                </span>
              </div>
            </div>
          </div>

          <div className="client-header-actions">
            <button
              className="btn-primary"
              onClick={() => navigate(`/program-builder?clientId=${clientId}`)}
            >
              <span className="button-icon">➕</span>
              Build New Program
            </button>
            <button
              className="btn-secondary"
              onClick={() => navigate(`/program-builder?clientId=${clientId}`)}
            >
              <span className="button-icon">📋</span>
              Build Program
            </button>
            <button className="btn-secondary">
              <span className="button-icon">✉️</span>
              Message Client
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <div className="stat-value">{client.active_programs}</div>
            <div className="stat-label">Active Programs</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <div className="stat-value">{client.completed_programs}</div>
            <div className="stat-label">Completed Programs</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💪</div>
          <div className="stat-content">
            <div className="stat-value">{client.total_workouts}</div>
            <div className="stat-label">Total Workouts</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📈</div>
          <div className="stat-content">
            <div className="stat-value">{Object.keys(oneRepMaxes).length}</div>
            <div className="stat-label">Recorded 1RMs</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs-container">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={`tab ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            Profile
          </button>
          <button
            className={`tab ${activeTab === 'programs' ? 'active' : ''}`}
            onClick={() => setActiveTab('programs')}
          >
            Programs
          </button>
          <button
            className={`tab ${activeTab === 'progress' ? 'active' : ''}`}
            onClick={() => setActiveTab('progress')}
          >
            Progress
          </button>
        </div>

        <div className="tab-content">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="overview-tab">
              <div className="overview-grid">
                {/* One Rep Maxes */}
                <div className="info-card">
                  <div className="info-card-header">
                    <h3>💪 One Rep Maxes</h3>
                    <button className="btn-sm btn-secondary" onClick={() => openOrmModal()}>+ Add 1RM</button>
                  </div>
                  <div className="info-card-body">
                    {Object.keys(oneRepMaxes).length === 0 ? (
                      <div className="empty-message">
                        <p>No 1RMs recorded yet</p>
                        <button className="btn-link" onClick={() => openOrmModal()}>Add first 1RM →</button>
                      </div>
                    ) : (
                      <div className="one-rm-list">
                        {Object.entries(oneRepMaxes).map(([exercise, data]) => {
                          const orm = data as OneRepMax;
                          return (
                            <div
                              key={exercise}
                              className="one-rm-item"
                              style={{ cursor: 'pointer' }}
                              onClick={() => openOrmModal(exercise, orm)}
                              title="Click to update"
                            >
                              <div className="one-rm-name">
                                {exercise}
                                {orm.verified && <span className="verified-badge">✓</span>}
                              </div>
                              <div className="one-rm-value">
                                {orm.weight} {orm.unit}
                              </div>
                              <div className="one-rm-date">
                                {formatDate(orm.tested_date)}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>

                {/* Fitness Goals */}
                <div className="info-card">
                  <div className="info-card-header">
                    <h3>🎯 Fitness Goals</h3>
                    <button className="btn-sm btn-secondary" onClick={() => setEditSection('fitness_goals')}>Edit</button>
                  </div>
                  <div className="info-card-body">
                    {fitnessGoals.primary_goal ? (
                      <div className="goals-content">
                        <div className="goal-item">
                          <span className="goal-label">Primary Goal:</span>
                          <span className="goal-value">
                            {fitnessGoals.primary_goal?.replace('_', ' ').toUpperCase()}
                          </span>
                        </div>
                        {fitnessGoals.specific_goals && (
                          <div className="goal-item">
                            <span className="goal-label">Details:</span>
                            <span className="goal-value">{fitnessGoals.specific_goals}</span>
                          </div>
                        )}
                        {fitnessGoals.target_date && (
                          <div className="goal-item">
                            <span className="goal-label">Target Date:</span>
                            <span className="goal-value">
                              {formatDate(fitnessGoals.target_date)}
                            </span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="empty-message">
                        <p>No fitness goals set</p>
                        <button className="btn-link">Set goals →</button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Training Preferences */}
                <div className="info-card">
                  <div className="info-card-header">
                    <h3>⚙️ Training Preferences</h3>
                    <button className="btn-sm btn-secondary" onClick={() => setEditSection('training_preferences')}>Edit</button>
                  </div>
                  <div className="info-card-body">
                    {trainingPrefs.available_days_per_week ? (
                      <div className="prefs-content">
                        <div className="pref-item">
                          <span className="pref-icon">📅</span>
                          <span>
                            {trainingPrefs.available_days_per_week} days per week available
                          </span>
                        </div>
                        {trainingPrefs.session_duration && (
                          <div className="pref-item">
                            <span className="pref-icon">⏱️</span>
                            <span>{trainingPrefs.session_duration} min sessions</span>
                          </div>
                        )}
                        {trainingPrefs.gym_access && (
                          <div className="pref-item">
                            <span className="pref-icon">🏋️</span>
                            <span>
                              {trainingPrefs.gym_access.replace('_', ' ').toUpperCase()}
                            </span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="empty-message">
                        <p>No training preferences set</p>
                        <button className="btn-link">Set preferences →</button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Health & Injuries */}
                <div className="info-card">
                  <div className="info-card-header">
                    <h3>🏥 Health Information</h3>
                    <button className="btn-sm btn-secondary" onClick={() => setEditSection('health_info')}>Edit</button>
                  </div>
                  <div className="info-card-body">
                    <div className="health-content">
                      <div className="health-item">
                        <span className="health-label">Medical Clearance:</span>
                        <span
                          className={`clearance-badge ${
                            healthInfo.medical_clearance ? 'cleared' : 'not-cleared'
                          }`}
                        >
                          {healthInfo.medical_clearance ? '✓ Cleared' : '⚠️ Not Cleared'}
                        </span>
                      </div>
                      {healthInfo.injuries && healthInfo.injuries.length > 0 && (
                        <div className="health-item">
                          <span className="health-label">Active Injuries:</span>
                          <div className="injuries-list">
                            {healthInfo.injuries.map((injury: any, index: number) => (
                              <div key={index} className="injury-tag">
                                {injury.injury} ({injury.recovery_status})
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div className="profile-tab">
              <div className="profile-sections">
                {/* Basic Info */}
                <div className="profile-section">
                  <div className="section-header">
                    <h3>Basic Information</h3>
                    <button className="btn-sm btn-secondary" onClick={() => setEditSection('basic_info')}>Edit</button>
                  </div>
                  <div className="section-content">
                    <div className="info-row">
                      <span className="info-label">Name:</span>
                      <span className="info-value">
                        {basicInfo.first_name || 'Not set'} {basicInfo.last_name || ''}
                      </span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Email:</span>
                      <span className="info-value">{client.email}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Phone:</span>
                      <span className="info-value">
                        {basicInfo.phone_number || 'Not set'}
                      </span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Date of Birth:</span>
                      <span className="info-value">
                        {formatDate(basicInfo.date_of_birth)}
                      </span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Gender:</span>
                      <span className="info-value">{basicInfo.gender || 'Not set'}</span>
                    </div>
                  </div>
                </div>

                {/* Anthropometrics */}
                <div className="profile-section">
                  <div className="section-header">
                    <h3>Body Measurements</h3>
                    <button className="btn-sm btn-secondary" onClick={() => setEditSection('anthropometrics')}>Edit</button>
                  </div>
                  <div className="section-content">
                    <div className="info-row">
                      <span className="info-label">Current Weight:</span>
                      <span className="info-value">
                        {anthropometrics.current_weight
                          ? `${anthropometrics.current_weight} ${
                              anthropometrics.weight_unit || 'lbs'
                            }`
                          : 'Not set'}
                      </span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Height:</span>
                      <span className="info-value">
                        {anthropometrics.current_height
                          ? `${anthropometrics.current_height} ${
                              anthropometrics.height_unit || 'inches'
                            }`
                          : 'Not set'}
                      </span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Body Fat %:</span>
                      <span className="info-value">
                        {anthropometrics.body_fat_percentage
                          ? `${anthropometrics.body_fat_percentage}%`
                          : 'Not set'}
                      </span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Goal Weight:</span>
                      <span className="info-value">
                        {anthropometrics.goal_weight
                          ? `${anthropometrics.goal_weight} ${
                              anthropometrics.weight_unit || 'lbs'
                            }`
                          : 'Not set'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Training Experience */}
                <div className="profile-section">
                  <div className="section-header">
                    <h3>Training Experience</h3>
                    <button className="btn-sm btn-secondary" onClick={() => setEditSection('training_experience')}>Edit</button>
                  </div>
                  <div className="section-content">
                    <div className="info-row">
                      <span className="info-label">Experience Level:</span>
                      <span className="info-value">
                        {trainingExp.overall_experience_level?.toUpperCase() || 'Not set'}
                      </span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Years Training:</span>
                      <span className="info-value">
                        {trainingExp.years_training || 'Not set'}
                      </span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Training Frequency:</span>
                      <span className="info-value">
                        {trainingExp.current_training_frequency
                          ? `${trainingExp.current_training_frequency} days/week`
                          : 'Not set'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Programs Tab */}
          {activeTab === 'programs' && (
            <div className="programs-tab">
              {programsLoading ? (
                <div className="loading-state">
                  <div className="spinner"></div>
                  <p>Loading programs...</p>
                </div>
              ) : programs.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">📋</div>
                  <h3>No Programs Yet</h3>
                  <p>Assign a program template to this client to get started.</p>
                  <button
                    className="btn-primary"
                    onClick={() => navigate(`/program-builder?clientId=${clientId}`)}
                  >
                    <span className="button-icon">➕</span>
                    Build Program
                  </button>
                </div>
              ) : (() => {
                const filteredPrograms = programs.filter(program => showCancelledPrograms || program.status !== 'cancelled');
                return (
                <>
                  {/* Filter Toggle */}
                  <div className="programs-header">
                    <h2>Assigned Programs</h2>
                    <label className="toggle-cancelled">
                      <input
                        type="checkbox"
                        checked={showCancelledPrograms}
                        onChange={(e) => setShowCancelledPrograms(e.target.checked)}
                      />
                      <span>Show cancelled programs</span>
                    </label>
                  </div>

                  {filteredPrograms.length === 0 ? (
                    <div className="empty-state">
                      <div className="empty-icon">📋</div>
                      <h3>All Programs Cancelled</h3>
                      <p>All assigned programs have been cancelled. Check "Show cancelled programs" to view them, or assign a new program.</p>
                      <button
                        className="btn-primary"
                        onClick={() => navigate(`/program-builder?clientId=${clientId}`)}
                      >
                        <span className="button-icon">➕</span>
                        Build Program
                      </button>
                    </div>
                  ) : (
                  <div className="programs-list">
                  {filteredPrograms.map((program) => (
                    <div key={program.assignment_id} className="program-card">
                      <div className="program-card-header">
                        <div>
                          <h3>{program.assignment_name || program.program_name}</h3>
                          {program.assignment_name && (
                            <p className="program-template-name">{program.program_name}</p>
                          )}
                        </div>
                        <span className={`status-badge status-${program.status}`}>
                          {program.status.replace('_', ' ')}
                        </span>
                      </div>

                      <div className="program-card-body">
                        <div className="program-meta">
                          <span>
                            <strong>{program.duration_weeks}</strong> weeks
                          </span>
                          <span>•</span>
                          <span>
                            <strong>{program.days_per_week}</strong> days/week
                          </span>
                          <span>•</span>
                          <span>
                            Week <strong>{program.current_week}</strong> of {program.duration_weeks}
                          </span>
                        </div>

                        <div className="program-progress">
                          <div className="progress-bar">
                            <div
                              className="progress-fill"
                              style={{ width: `${program.progress_percentage}%` }}
                            ></div>
                          </div>
                          <span className="progress-text">{Math.round(program.progress_percentage)}% complete</span>
                        </div>

                        <div className="program-dates">
                          <div>
                            <span className="date-label">Start:</span>
                            <span>{formatDate(program.start_date)}</span>
                          </div>
                          <div>
                            <span className="date-label">End:</span>
                            <span>{formatDate(program.end_date)}</span>
                          </div>
                          {program.actual_completion_date && (
                            <div>
                              <span className="date-label">Completed:</span>
                              <span>{formatDate(program.actual_completion_date)}</span>
                            </div>
                          )}
                        </div>

                        <div className="program-coach">
                          <span className="coach-label">Assigned by:</span>
                          <span>{program.assigned_by_name}</span>
                        </div>
                      </div>

                      <div className="program-card-footer">
                        {program.program_status === 'draft' ? (
                          <button
                            className="btn-primary btn-sm"
                            onClick={() => navigate(`/programs/draft/${program.program_id}?clientId=${clientId}`)}
                          >
                            Review Draft
                          </button>
                        ) : (
                          <button
                            className="btn-secondary btn-sm"
                            onClick={() => navigate(`/programs/${program.program_id}`)}
                          >
                            View Details
                          </button>
                        )}
                        {program.status === 'in_progress' && (
                          <button
                            className="btn-primary btn-sm"
                            onClick={() => navigate(`/my-programs/${program.assignment_id}`)}
                          >
                            View Workouts
                          </button>
                        )}
                        {program.status !== 'cancelled' && (
                          <button
                            className="btn-danger btn-sm"
                            onClick={() => handleDeleteProgram(program.assignment_id, program.assignment_name || program.program_name)}
                            style={{ marginLeft: 'auto' }}
                          >
                            Remove
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                  )}
                </>
                );
              })()}
            </div>
          )}

          {/* Progress Tab */}
          {activeTab === 'progress' && (
            <div className="progress-tab">
              {progressLoading ? (
                <div className="loading-state">
                  <div className="spinner" />
                  <p>Loading workout history…</p>
                </div>
              ) : progressWorkouts.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">📈</div>
                  <h3>No Progress Data Yet</h3>
                  <p>Workout history will appear here once the client starts logging sessions.</p>
                </div>
              ) : (() => {
                const completed = progressWorkouts.filter(w => w.status === 'completed');
                const skipped   = progressWorkouts.filter(w => w.status === 'skipped');
                const totalLogged = progressWorkouts.length;
                const adherencePct = totalLogged > 0
                  ? Math.round((completed.length / totalLogged) * 100) : 0;

                // Last 8 weeks activity: bucket by ISO week
                const weekBuckets: Record<string, { completed: number; skipped: number }> = {};
                progressWorkouts.forEach(w => {
                  const d = new Date(w.workout_date);
                  // simple week key: year-weekNumber
                  const startOfYear = new Date(d.getFullYear(), 0, 1);
                  const weekNum = Math.ceil(((d.getTime() - startOfYear.getTime()) / 86400000 + startOfYear.getDay() + 1) / 7);
                  const key = `${d.getFullYear()}-W${String(weekNum).padStart(2, '0')}`;
                  if (!weekBuckets[key]) weekBuckets[key] = { completed: 0, skipped: 0 };
                  if (w.status === 'completed') weekBuckets[key].completed++;
                  else if (w.status === 'skipped') weekBuckets[key].skipped++;
                });
                const weekKeys = Object.keys(weekBuckets).sort().slice(-8);

                return (
                  <>
                    {/* Summary cards */}
                    <div className="progress-stats-grid">
                      <div className="progress-stat-card">
                        <span className="progress-stat-value">{totalLogged}</span>
                        <span className="progress-stat-label">Total Sessions</span>
                      </div>
                      <div className="progress-stat-card">
                        <span className="progress-stat-value">{completed.length}</span>
                        <span className="progress-stat-label">Completed</span>
                      </div>
                      <div className="progress-stat-card">
                        <span className="progress-stat-value">{skipped.length}</span>
                        <span className="progress-stat-label">Skipped</span>
                      </div>
                      <div className="progress-stat-card progress-stat-highlight">
                        <span className="progress-stat-value">{adherencePct}%</span>
                        <span className="progress-stat-label">Adherence</span>
                      </div>
                    </div>

                    {/* Weekly activity chart (simple bar-style) */}
                    {weekKeys.length > 0 && (
                      <div className="progress-weekly-section">
                        <h3 className="progress-section-title">Weekly Activity (last 8 weeks)</h3>
                        <div className="progress-weekly-bars">
                          {weekKeys.map(wk => {
                            const b = weekBuckets[wk];
                            const total = b.completed + b.skipped;
                            return (
                              <div key={wk} className="progress-week-col">
                                <div className="progress-week-bar-wrap">
                                  <div
                                    className="progress-week-bar completed-bar"
                                    style={{ height: `${Math.min(b.completed * 24, 96)}px` }}
                                    title={`${b.completed} completed`}
                                  />
                                  {b.skipped > 0 && (
                                    <div
                                      className="progress-week-bar skipped-bar"
                                      style={{ height: `${Math.min(b.skipped * 24, 48)}px` }}
                                      title={`${b.skipped} skipped`}
                                    />
                                  )}
                                </div>
                                <span className="progress-week-label">{total}</span>
                                <span className="progress-week-key">{wk.split('-W')[1] ? `W${wk.split('-W')[1]}` : wk}</span>
                              </div>
                            );
                          })}
                        </div>
                        <div className="progress-legend">
                          <span className="legend-dot completed-dot" /> Completed
                          <span className="legend-dot skipped-dot" style={{ marginLeft: 12 }} /> Skipped
                        </div>
                      </div>
                    )}

                    {/* Workout history list */}
                    <div className="progress-history-section">
                      <h3 className="progress-section-title">Session History</h3>
                      <div className="progress-history-list">
                        {progressWorkouts.map(w => (
                          <div key={w.id} className="progress-history-row">
                            <span className={`progress-status-dot dot-${w.status}`} title={w.status} />
                            <div className="progress-history-info">
                              <span className="progress-history-date">
                                {new Date(w.workout_date).toLocaleDateString(undefined, {
                                  weekday: 'short', month: 'short', day: 'numeric',
                                })}
                              </span>
                              {w.program_name && (
                                <span className="progress-history-program">{w.program_name}</span>
                              )}
                            </div>
                            <div className="progress-history-meta">
                              {w.duration_minutes && (
                                <span className="progress-history-duration">{w.duration_minutes} min</span>
                              )}
                              <span className={`progress-history-status status-${w.status}`}>{w.status}</span>
                            </div>
                            {w.notes && (
                              <span className="progress-history-notes" title={w.notes}>
                                {w.notes.length > 60 ? w.notes.slice(0, 60) + '…' : w.notes}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                );
              })()}
            </div>
          )}
        </div>
      </div>

      {/* Edit Profile Modal */}
      {editSection && client && (
        <EditProfileModal
          clientId={clientId!}
          section={editSection}
          currentProfile={client.profile || {}}
          onClose={() => setEditSection(null)}
          onSaved={updated => {
            setClient(updated);
            setEditSection(null);
          }}
        />
      )}

      {/* Add / Update 1RM Modal */}
      {showOrmModal && (
        <div className="modal-overlay" onClick={() => setShowOrmModal(false)}>
          <div className="modal-content" style={{ maxWidth: 400 }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{ormForm.exercise_name ? `Update ${ormForm.exercise_name}` : 'Add 1RM'}</h2>
              <button className="modal-close" onClick={() => setShowOrmModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              {ormError && <div className="edit-error-banner">{ormError}</div>}
              <div className="form-group">
                <label>Exercise Name</label>
                <input
                  type="text"
                  placeholder="e.g. Squat, Bench Press, Deadlift"
                  value={ormForm.exercise_name}
                  onChange={e => setOrmForm(f => ({ ...f, exercise_name: e.target.value }))}
                  autoFocus
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Weight</label>
                  <input
                    type="number"
                    min="1"
                    step="0.5"
                    placeholder="0"
                    value={ormForm.weight || ''}
                    onChange={e => setOrmForm(f => ({ ...f, weight: parseFloat(e.target.value) || 0 }))}
                  />
                </div>
                <div className="form-group">
                  <label>Unit</label>
                  <select
                    value={ormForm.unit}
                    onChange={e => setOrmForm(f => ({ ...f, unit: e.target.value as 'lbs' | 'kg' }))}
                  >
                    <option value="lbs">lbs</option>
                    <option value="kg">kg</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>Test Date</label>
                <input
                  type="date"
                  value={ormForm.tested_date}
                  onChange={e => setOrmForm(f => ({ ...f, tested_date: e.target.value }))}
                />
              </div>
              <div className="form-group checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={ormForm.verified || false}
                    onChange={e => setOrmForm(f => ({ ...f, verified: e.target.checked }))}
                  />
                  <span>Verified (tested under supervision)</span>
                </label>
              </div>
              <div className="modal-footer">
                <button className="btn-secondary" onClick={() => setShowOrmModal(false)} disabled={ormSaving}>
                  Cancel
                </button>
                <button className="btn-primary" onClick={handleOrmSave} disabled={ormSaving}>
                  {ormSaving ? 'Saving…' : 'Save 1RM'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
