import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { getUserDisplayName } from '../types/user';
import { useEffect, useState } from 'react';
import { getCoachStats } from '../services/coaches';
import type { CoachStats } from '../services/coaches';
import './Dashboard.css';

export default function CoachDashboard() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const displayName = getUserDisplayName(user);

  const [stats, setStats] = useState<CoachStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch coach statistics on mount
  useEffect(() => {
    const loadStats = async () => {
      try {
        setLoading(true);
        const data = await getCoachStats();
        setStats(data);
        setError(null);
      } catch (err) {
        console.error('Failed to load coach stats:', err);
        setError('Failed to load statistics');
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, []);

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
          <p className="card-value">
            {loading ? '--' : error ? '--' : stats?.active_clients ?? 0}
          </p>
          <p className="card-label">Active clients</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">📊</div>
          <h3>Active Programs</h3>
          <p className="card-value">
            {loading ? '--' : error ? '--' : stats?.active_programs ?? 0}
          </p>
          <p className="card-label">Assigned to clients</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon"></div>
          <h3>Total Clients</h3>
          <p className="card-value">
            {loading ? '--' : error ? '--' : stats?.total_clients ?? 0}
          </p>
          <p className="card-label">All time</p>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>{t('dashboard.quickActions')}</h2>
        <div className="action-buttons">
          <button className="action-button primary" onClick={() => navigate('/program-builder')}>
            <span className="button-icon">➕</span>
            {t('dashboard.createProgram')}
          </button>
          <button className="action-button secondary" onClick={() => navigate('/clients')}>
            <span className="button-icon">👤</span>
            View Clients
          </button>
          <button className="action-button secondary" onClick={() => navigate('/programs')}>
            <span className="button-icon">📋</span>
            My Programs
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
