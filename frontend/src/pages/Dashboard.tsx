import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './Dashboard.css';

export default function Dashboard() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>{t('dashboard.welcome')}</h1>
        <p>{t('dashboard.subtitle')}</p>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <div className="card-icon">📊</div>
          <h3>{t('dashboard.totalPrograms')}</h3>
          <p className="card-value">24</p>
          <p className="card-label">{t('dashboard.activeProgramsCount')}</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">👥</div>
          <h3>{t('dashboard.activeClients')}</h3>
          <p className="card-value">156</p>
          <p className="card-label">{t('dashboard.currentlyEnrolled')}</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">✅</div>
          <h3>{t('dashboard.completedToday')}</h3>
          <p className="card-value">47</p>
          <p className="card-label">{t('dashboard.workoutSessions')}</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">📈</div>
          <h3>{t('dashboard.avgProgress')}</h3>
          <p className="card-value">87%</p>
          <p className="card-label">{t('dashboard.completionRate')}</p>
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
            {t('dashboard.addClient')}
          </button>
          <button className="action-button secondary">
            <span className="button-icon">📋</span>
            {t('dashboard.viewReports')}
          </button>
          <button className="action-button secondary">
            <span className="button-icon">⚙️</span>
            {t('dashboard.settings')}
          </button>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>{t('dashboard.recentActivity')}</h2>
        <div className="activity-list">
          <div className="activity-item">
            <div className="activity-icon">🎯</div>
            <div className="activity-details">
              <p className="activity-title">New program created: "Strength Building 101"</p>
              <p className="activity-time">2 hours ago</p>
            </div>
          </div>
          <div className="activity-item">
            <div className="activity-icon">✨</div>
            <div className="activity-details">
              <p className="activity-title">Client "John Doe" completed Week 4</p>
              <p className="activity-time">5 hours ago</p>
            </div>
          </div>
          <div className="activity-item">
            <div className="activity-icon">📝</div>
            <div className="activity-details">
              <p className="activity-title">Updated program: "Advanced HIIT Training"</p>
              <p className="activity-time">1 day ago</p>
            </div>
          </div>
          <div className="activity-item">
            <div className="activity-icon">🎉</div>
            <div className="activity-details">
              <p className="activity-title">Client "Sarah Smith" achieved goal weight</p>
              <p className="activity-time">2 days ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
