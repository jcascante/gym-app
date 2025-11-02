import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Welcome to GymPro</h1>
        <p>Manage your training programs and track client progress</p>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <div className="card-icon">📊</div>
          <h3>Total Programs</h3>
          <p className="card-value">24</p>
          <p className="card-label">Active training programs</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">👥</div>
          <h3>Active Clients</h3>
          <p className="card-value">156</p>
          <p className="card-label">Currently enrolled</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">✅</div>
          <h3>Completed Today</h3>
          <p className="card-value">47</p>
          <p className="card-label">Workout sessions</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">📈</div>
          <h3>Avg. Progress</h3>
          <p className="card-value">87%</p>
          <p className="card-label">Client completion rate</p>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>Quick Actions</h2>
        <div className="action-buttons">
          <button className="action-button primary" onClick={() => navigate('/program-builder')}>
            <span className="button-icon">➕</span>
            Create New Program
          </button>
          <button className="action-button secondary">
            <span className="button-icon">👤</span>
            Add Client
          </button>
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
