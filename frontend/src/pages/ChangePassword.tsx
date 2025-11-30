import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { changePassword } from '../services/auth';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import './ChangePassword.css';

export default function ChangePassword() {
  const { t } = useTranslation();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Check if this is a forced password change (from login)
  const isForced = location.state?.passwordMustBeChanged === true;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Validate new password
    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters long');
      return;
    }

    // Validate password confirmation
    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    // Validate new password is different
    if (currentPassword === newPassword) {
      setError('New password must be different from current password');
      return;
    }

    setIsLoading(true);

    try {
      const response = await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });

      setSuccess(response.message || 'Password changed successfully!');

      // Wait a moment to show success message, then redirect
      setTimeout(() => {
        if (isForced) {
          // If forced, navigate to dashboard after successful change
          navigate('/dashboard');
        } else {
          // If voluntary change, go back to previous page
          navigate(-1);
        }
      }, 2000);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to change password'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    if (isForced) {
      // If forced, logout since they can't access anything else
      logout();
      navigate('/login');
    } else {
      // If voluntary, go back
      navigate(-1);
    }
  };

  return (
    <div className="change-password-container">
      <div className="change-password-box">
        <div className="change-password-header">
          <h1>{isForced ? 'Change Password Required' : 'Change Password'}</h1>
          {isForced && (
            <p className="warning-message">
              You must change your temporary password before accessing the application.
            </p>
          )}
          {!isForced && (
            <p>Update your account password</p>
          )}
        </div>

        <form onSubmit={handleSubmit} className="change-password-form">
          <div className="form-group">
            <label htmlFor="currentPassword">Current Password</label>
            <input
              type="password"
              id="currentPassword"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="Enter your current password"
              required
              autoComplete="current-password"
            />
          </div>

          <div className="form-group">
            <label htmlFor="newPassword">New Password</label>
            <input
              type="password"
              id="newPassword"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Enter your new password"
              required
              minLength={8}
              autoComplete="new-password"
            />
            <small className="form-hint">Minimum 8 characters</small>
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm New Password</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your new password"
              required
              minLength={8}
              autoComplete="new-password"
            />
          </div>

          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          <div className="form-actions">
            <button
              type="submit"
              className="submit-button"
              disabled={isLoading}
            >
              {isLoading ? 'Changing Password...' : 'Change Password'}
            </button>

            <button
              type="button"
              className="cancel-button"
              onClick={handleCancel}
              disabled={isLoading}
            >
              {isForced ? 'Logout' : 'Cancel'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
