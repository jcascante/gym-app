import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { getUserDisplayName } from '../types/user';
import './Dashboard.css';

export default function CoachDashboard() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const displayName = getUserDisplayName(user);

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>{t('dashboard.welcome')}, Coach {displayName}</h1>
        <p>Manage your clients and training programs</p>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <div className="card-icon">👥</div>
          <h3>My Clients</h3>
          <p className="card-value">--</p>
          <p className="card-label">Active clients</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">📊</div>
          <h3>My Programs</h3>
          <p className="card-value">--</p>
          <p className="card-label">Active programs</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">✅</div>
          <h3>Today's Sessions</h3>
          <p className="card-value">--</p>
          <p className="card-label">Scheduled sessions</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">📈</div>
          <h3>Completion Rate</h3>
          <p className="card-value">--%</p>
          <p className="card-label">This week</p>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>{t('dashboard.quickActions')}</h2>
        <div className="action-buttons">
          <button className="action-button primary" onClick={() => navigate('/program-builder')}>
            <span className="button-icon">➕</span>
            {t('dashboard.createProgram')}
          </button>
          <button className="action-button secondary">
            <span className="button-icon">👤</span>
            View Clients
          </button>
          <button className="action-button secondary">
            <span className="button-icon">📋</span>
            My Programs
          </button>
          <button className="action-button secondary">
            <span className="button-icon">📅</span>
            Schedule
          </button>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>Recent Activity</h2>
        <div className="activity-list">
          <div className="activity-item">
            <div className="activity-icon">🎯</div>
            <div className="activity-details">
              <p className="activity-title">Client completed workout session</p>
              <p className="activity-time">1 hour ago</p>
            </div>
          </div>
          <div className="activity-item">
            <div className="activity-icon">✨</div>
            <div className="activity-details">
              <p className="activity-title">New client assigned to you</p>
              <p className="activity-time">3 hours ago</p>
            </div>
          </div>
          <div className="activity-item">
            <div className="activity-icon">📝</div>
            <div className="activity-details">
              <p className="activity-title">Program update saved</p>
              <p className="activity-time">1 day ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
