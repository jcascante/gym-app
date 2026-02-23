import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { getUserDisplayName } from '../types/user';
import { useEffect, useState } from 'react';
import { getWorkoutStats, getRecentWorkouts, createWorkout } from '../services/workouts';
import type { WorkoutStats, RecentWorkout } from '../services/workouts';
import { getMyPrograms } from '../services/programAssignments';
import './Dashboard.css';

export default function ClientDashboard() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const displayName = getUserDisplayName(user);

  const [stats, setStats] = useState<WorkoutStats | null>(null);
  const [recentWorkouts, setRecentWorkouts] = useState<RecentWorkout[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  

  // Fetch workout statistics and recent workouts on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [statsData, recentData] = await Promise.all([
          getWorkoutStats(),
          getRecentWorkouts(7, 5),
        ]);

        setStats(statsData);
        setRecentWorkouts(recentData || []);
      } catch (err) {
        console.error('Failed to load dashboard data', err);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>{t('dashboard.welcome')}, {displayName}</h1>
        <p>Track your fitness journey and progress</p>
      </div>
      

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <div className="card-icon">📊</div>
          <h3>Total Workouts</h3>
          <p className="card-value">
            {loading ? '--' : error ? '--' : stats?.total_workouts ?? 0}
          </p>
          <p className="card-label">All time</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">✅</div>
          <h3>Workouts Completed</h3>
          <p className="card-value">
            {loading ? '--' : error ? '--' : stats?.completed_workouts ?? 0}
          </p>
          <p className="card-label">Finished sessions</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">⏭️</div>
          <h3>Workouts Skipped</h3>
          <p className="card-value">
            {loading ? '--' : error ? '--' : stats?.skipped_workouts ?? 0}
          </p>
          <p className="card-label">Missed sessions</p>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">📈</div>
          <h3>Last Workout</h3>
          <p className="card-value">
            {loading ? '--' : error ? '--' : (stats?.last_workout_date ? new Date(stats.last_workout_date).toLocaleDateString() : 'Never')}
          </p>
          <p className="card-label">Most recent</p>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>Quick Actions</h2>
        <div className="action-buttons">
          <button
            className="action-button primary"
            onClick={async () => {
              try {
                setStarting(true);
                const resp = await getMyPrograms();
                const firstAssignment = resp.programs && resp.programs.length > 0 ? resp.programs[0] : null;
                if (!firstAssignment) {
                  alert('No active program assignment found.');
                  setStarting(false);
                  return;
                }

                const tempId = `tmp-${Date.now()}`;
                const now = new Date().toISOString();

                const optimistic: RecentWorkout = {
                  id: tempId,
                  workout_date: now,
                  status: 'completed',
                  program_name: firstAssignment.program_name,
                  assignment_name: firstAssignment.assignment_name,
                };

                setRecentWorkouts((prev) => [optimistic, ...(prev || [])].slice(0, 10));
                setStats((s) => s ? { ...s, total_workouts: s.total_workouts + 1, completed_workouts: s.completed_workouts + 1, last_workout_date: now } : s);

                const created = await createWorkout(firstAssignment.assignment_id, 'completed', undefined, 'Great session', now);

                setRecentWorkouts((prev) => [ { ...created }, ...(prev || []).filter((w) => w.id !== tempId) ].slice(0, 10));
              } catch (err) {
                console.error('Failed to start workout:', err);
                setError('Failed to log workout');
              } finally {
                setStarting(false);
              }
            }}
          >
            <span className="button-icon">🏋️</span>
            Start Today's Workout
          </button>
          <button
            className="action-button secondary"
            onClick={() => navigate('/my-programs')}
          >
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
          {recentWorkouts.length === 0 ? (
            <p style={{ textAlign: 'center', color: '#666' }}>
              No recent workouts. Start tracking your first workout!
            </p>
          ) : (
            recentWorkouts.map((workout) => (
              <div key={workout.id} className="activity-item">
                <div className="activity-icon">
                  {workout.status === 'completed' ? '✅' : workout.status === 'skipped' ? '⏭️' : '📅'}
                </div>
                <div className="activity-details">
                  <p className="activity-title">
                    {workout.status === 'completed' ? 'Completed' : workout.status === 'skipped' ? 'Skipped' : 'Scheduled'}: {workout.program_name || 'Workout'}
                  </p>
                  <p className="activity-time">
                    {new Date(workout.workout_date).toLocaleDateString()} at {new Date(workout.workout_date).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
