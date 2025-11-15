import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { UserRole } from '../types/user';
import AdminDashboard from './AdminDashboard';
import CoachDashboard from './CoachDashboard';
import ClientDashboard from './ClientDashboard';

export default function Dashboard() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Redirect to role-specific dashboard
  switch (user.role) {
    case UserRole.APPLICATION_SUPPORT:
    case UserRole.SUBSCRIPTION_ADMIN:
      return <AdminDashboard />;
    case UserRole.COACH:
      return <CoachDashboard />;
    case UserRole.CLIENT:
      return <ClientDashboard />;
    default:
      return <Navigate to="/login" replace />;
  }
}
