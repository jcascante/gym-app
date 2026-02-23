import { useState } from 'react';
import { updateClientProfile, type ClientProfile, type ClientDetailResponse } from '../services/clients';
import { ApiError } from '../services/api';
import './EditProfileModal.css';

export type ProfileSection =
  | 'basic_info'
  | 'anthropometrics'
  | 'fitness_goals'
  | 'training_preferences'
  | 'health_info'
  | 'training_experience';

const SECTION_LABELS: Record<ProfileSection, string> = {
  basic_info: 'Basic Information',
  anthropometrics: 'Body Measurements',
  fitness_goals: 'Fitness Goals',
  training_preferences: 'Training Preferences',
  health_info: 'Health Information',
  training_experience: 'Training Experience',
};

interface EditProfileModalProps {
  clientId: string;
  section: ProfileSection;
  currentProfile: ClientProfile;
  onClose: () => void;
  onSaved: (updated: ClientDetailResponse) => void;
}

export default function EditProfileModal({
  clientId,
  section,
  currentProfile,
  onClose,
  onSaved,
}: EditProfileModalProps) {
  const [draft, setDraft] = useState<ClientProfile[typeof section]>(
    currentProfile[section] ? { ...(currentProfile[section] as object) } : {}
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const setField = (key: string, value: unknown) => {
    setDraft(prev => ({ ...(prev as object), [key]: value }));
  };

  const get = (key: string): unknown => {
    return (draft as Record<string, unknown>)?.[key] ?? '';
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      const updated = await updateClientProfile(clientId, { [section]: draft });
      onSaved(updated);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to save. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content edit-profile-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Edit {SECTION_LABELS[section]}</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {error && (
            <div className="edit-error-banner">{error}</div>
          )}

          {section === 'basic_info' && (
            <div className="edit-fields">
              <div className="form-row">
                <div className="form-group">
                  <label>First Name</label>
                  <input type="text" value={String(get('first_name'))} onChange={e => setField('first_name', e.target.value)} placeholder="First name" />
                </div>
                <div className="form-group">
                  <label>Last Name</label>
                  <input type="text" value={String(get('last_name'))} onChange={e => setField('last_name', e.target.value)} placeholder="Last name" />
                </div>
              </div>
              <div className="form-group">
                <label>Phone Number</label>
                <input type="tel" value={String(get('phone_number'))} onChange={e => setField('phone_number', e.target.value)} placeholder="+1 (555) 000-0000" />
              </div>
              <div className="form-group">
                <label>Date of Birth</label>
                <input type="date" value={String(get('date_of_birth'))} onChange={e => setField('date_of_birth', e.target.value)} />
              </div>
              <div className="form-group">
                <label>Gender</label>
                <select value={String(get('gender'))} onChange={e => setField('gender', e.target.value)}>
                  <option value="">Not specified</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                  <option value="prefer_not_to_say">Prefer not to say</option>
                </select>
              </div>
            </div>
          )}

          {section === 'anthropometrics' && (
            <div className="edit-fields">
              <div className="form-row">
                <div className="form-group">
                  <label>Current Weight</label>
                  <input type="number" min="0" step="0.1" value={String(get('current_weight'))} onChange={e => setField('current_weight', e.target.value ? parseFloat(e.target.value) : '')} placeholder="0" />
                </div>
                <div className="form-group">
                  <label>Unit</label>
                  <select value={String(get('weight_unit') || 'lbs')} onChange={e => setField('weight_unit', e.target.value)}>
                    <option value="lbs">lbs</option>
                    <option value="kg">kg</option>
                  </select>
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Height</label>
                  <input type="number" min="0" step="0.1" value={String(get('current_height'))} onChange={e => setField('current_height', e.target.value ? parseFloat(e.target.value) : '')} placeholder="0" />
                </div>
                <div className="form-group">
                  <label>Height Unit</label>
                  <select value={String(get('height_unit') || 'inches')} onChange={e => setField('height_unit', e.target.value)}>
                    <option value="inches">inches</option>
                    <option value="cm">cm</option>
                  </select>
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Body Fat %</label>
                  <input type="number" min="0" max="100" step="0.1" value={String(get('body_fat_percentage'))} onChange={e => setField('body_fat_percentage', e.target.value ? parseFloat(e.target.value) : '')} placeholder="0" />
                </div>
                <div className="form-group">
                  <label>Goal Weight</label>
                  <input type="number" min="0" step="0.1" value={String(get('goal_weight'))} onChange={e => setField('goal_weight', e.target.value ? parseFloat(e.target.value) : '')} placeholder="0" />
                </div>
              </div>
            </div>
          )}

          {section === 'fitness_goals' && (
            <div className="edit-fields">
              <div className="form-group">
                <label>Primary Goal</label>
                <select value={String(get('primary_goal'))} onChange={e => setField('primary_goal', e.target.value)}>
                  <option value="">Not specified</option>
                  <option value="strength">Strength</option>
                  <option value="hypertrophy">Hypertrophy / Muscle Building</option>
                  <option value="fat_loss">Fat Loss</option>
                  <option value="athletic_performance">Athletic Performance</option>
                  <option value="general_fitness">General Fitness</option>
                  <option value="rehabilitation">Rehabilitation</option>
                </select>
              </div>
              <div className="form-group">
                <label>Specific Goals</label>
                <textarea rows={3} value={String(get('specific_goals'))} onChange={e => setField('specific_goals', e.target.value)} placeholder="Describe specific goals..." />
              </div>
              <div className="form-group">
                <label>Target Date</label>
                <input type="date" value={String(get('target_date'))} onChange={e => setField('target_date', e.target.value)} />
              </div>
              <div className="form-group">
                <label>Motivation</label>
                <textarea rows={2} value={String(get('motivation'))} onChange={e => setField('motivation', e.target.value)} placeholder="What motivates this client?" />
              </div>
            </div>
          )}

          {section === 'training_preferences' && (
            <div className="edit-fields">
              <div className="form-row">
                <div className="form-group">
                  <label>Days Available per Week</label>
                  <input type="number" min="1" max="7" value={String(get('available_days_per_week'))} onChange={e => setField('available_days_per_week', e.target.value ? parseInt(e.target.value) : '')} placeholder="3" />
                </div>
                <div className="form-group">
                  <label>Session Duration (min)</label>
                  <input type="number" min="15" step="15" value={String(get('session_duration'))} onChange={e => setField('session_duration', e.target.value ? parseInt(e.target.value) : '')} placeholder="60" />
                </div>
              </div>
              <div className="form-group">
                <label>Gym Access</label>
                <select value={String(get('gym_access'))} onChange={e => setField('gym_access', e.target.value)}>
                  <option value="">Not specified</option>
                  <option value="full_gym">Full Gym</option>
                  <option value="home_gym">Home Gym</option>
                  <option value="bodyweight_only">Bodyweight Only</option>
                  <option value="limited_equipment">Limited Equipment</option>
                </select>
              </div>
            </div>
          )}

          {section === 'health_info' && (
            <div className="edit-fields">
              <div className="form-group checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={Boolean(get('medical_clearance'))}
                    onChange={e => setField('medical_clearance', e.target.checked)}
                  />
                  <span>Medical clearance obtained</span>
                </label>
              </div>
              {Boolean(get('medical_clearance')) && (
                <div className="form-group">
                  <label>Clearance Date</label>
                  <input type="date" value={String(get('clearance_date'))} onChange={e => setField('clearance_date', e.target.value)} />
                </div>
              )}
              <p className="form-hint">To manage injuries and medical conditions, use the detailed health form.</p>
            </div>
          )}

          {section === 'training_experience' && (
            <div className="edit-fields">
              <div className="form-group">
                <label>Experience Level</label>
                <select value={String(get('overall_experience_level'))} onChange={e => setField('overall_experience_level', e.target.value)}>
                  <option value="">Not specified</option>
                  <option value="beginner">Beginner (0–1 year)</option>
                  <option value="novice">Novice (1–2 years)</option>
                  <option value="intermediate">Intermediate (2–5 years)</option>
                  <option value="advanced">Advanced (5–10 years)</option>
                  <option value="elite">Elite (10+ years)</option>
                </select>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Years Training</label>
                  <input type="number" min="0" step="0.5" value={String(get('years_training'))} onChange={e => setField('years_training', e.target.value ? parseFloat(e.target.value) : '')} placeholder="0" />
                </div>
                <div className="form-group">
                  <label>Current Frequency (days/wk)</label>
                  <input type="number" min="0" max="7" value={String(get('current_training_frequency'))} onChange={e => setField('current_training_frequency', e.target.value ? parseInt(e.target.value) : '')} placeholder="0" />
                </div>
              </div>
            </div>
          )}

          <div className="modal-footer">
            <button className="btn-secondary" onClick={onClose} disabled={saving}>
              Cancel
            </button>
            <button className="btn-primary" onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
