import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { getUserDisplayName } from '../types/user';
import './Dashboard.css';

export default function ClientDashboard() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const displayName = getUserDisplayName(user);

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>{t('dashboard.welcome')}, {displayName}</h1>
        <p>Track your fitness journey and progress</p>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <div className="card-icon">📊</div>
          <h3>My Programs</h3>
          <p className="card-value">--</p>
          <p className="card-label">Active programs</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">✅</div>
          <h3>Workouts Completed</h3>
          <p className="card-value">--</p>
          <p className="card-label">This week</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">🔥</div>
          <h3>Current Streak</h3>
          <p className="card-value">-- days</p>
          <p className="card-label">Keep it going!</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">📈</div>
          <h3>Overall Progress</h3>
          <p className="card-value">--%</p>
          <p className="card-label">Program completion</p>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>Quick Actions</h2>
        <div className="action-buttons">
          <button className="action-button primary">
            <span className="button-icon">🏋️</span>
            Start Today's Workout
          </button>
          <button className="action-button secondary">
            <span className="button-icon">📊</span>
            View My Programs
          </button>
          <button className="action-button secondary">
            <span className="button-icon">📈</span>
            Track Progress
          </button>
          <button className="action-button secondary">
            <span className="button-icon">👤</span>
            My Profile
          </button>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>Recent Activity</h2>
        <div className="activity-list">
          <div className="activity-item">
            <div className="activity-icon">✅</div>
            <div className="activity-details">
              <p className="activity-title">Completed: Upper Body Strength</p>
              <p className="activity-time">Today at 10:30 AM</p>
            </div>
          </div>
          <div className="activity-item">
            <div className="activity-icon">🎯</div>
            <div className="activity-details">
              <p className="activity-title">New program assigned: "Core Fundamentals"</p>
              <p className="activity-time">Yesterday</p>
            </div>
          </div>
          <div className="activity-item">
            <div className="activity-icon">🏆</div>
            <div className="activity-details">
              <p className="activity-title">Achievement unlocked: 7-day streak!</p>
              <p className="activity-time">2 days ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
