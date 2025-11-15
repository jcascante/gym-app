import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { getUserDisplayName, isSupport } from '../types/user';
import './Dashboard.css';

export default function AdminDashboard() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const displayName = getUserDisplayName(user);
  const isSupportUser = isSupport(user);

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>{t('dashboard.welcome')}, {displayName}</h1>
        <p>{isSupportUser ? 'Application Support Dashboard' : 'Subscription Admin Dashboard'}</p>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <div className="card-icon">👥</div>
          <h3>Total Users</h3>
          <p className="card-value">--</p>
          <p className="card-label">Across all roles</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">🏋️</div>
          <h3>Active Coaches</h3>
          <p className="card-value">--</p>
          <p className="card-label">Currently active</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">🎯</div>
          <h3>Active Clients</h3>
          <p className="card-value">--</p>
          <p className="card-label">Currently enrolled</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">📊</div>
          <h3>Total Programs</h3>
          <p className="card-value">--</p>
          <p className="card-label">Active programs</p>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>Admin Actions</h2>
        <div className="action-buttons">
          <button className="action-button primary">
            <span className="button-icon">➕</span>
            Add User
          </button>
          <button className="action-button secondary">
            <span className="button-icon">👥</span>
            Manage Users
          </button>
          {isSupportUser && (
            <>
              <button className="action-button secondary">
                <span className="button-icon">🏢</span>
                Manage Subscriptions
              </button>
              <button className="action-button secondary">
                <span className="button-icon">📍</span>
                Manage Locations
              </button>
            </>
          )}
          <button className="action-button secondary">
            <span className="button-icon">📋</span>
            View Reports
          </button>
          <button className="action-button secondary">
            <span className="button-icon">⚙️</span>
            Settings
          </button>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>Recent Activity</h2>
        <div className="activity-list">
          <div className="activity-item">
            <div className="activity-icon">👤</div>
            <div className="activity-details">
              <p className="activity-title">New user registered</p>
              <p className="activity-time">2 hours ago</p>
            </div>
          </div>
          <div className="activity-item">
            <div className="activity-icon">🎯</div>
            <div className="activity-details">
              <p className="activity-title">New program created</p>
              <p className="activity-time">5 hours ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
