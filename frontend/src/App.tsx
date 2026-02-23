import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import ChangePassword from './pages/ChangePassword';
import Dashboard from './pages/Dashboard';
import ProgramBuilder from './pages/ProgramBuilder';
import Clients from './pages/Clients';
import ClientDetail from './pages/ClientDetail';
import Programs from './pages/Programs';
import MyPrograms from './pages/MyPrograms';
import ProgramDetails from './pages/ProgramDetails';
import ProgramTemplateView from './pages/ProgramTemplateView';
import ProgramDraftReview from './pages/ProgramDraftReview';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/change-password"
            element={
              <ProtectedRoute>
                <ChangePassword />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/program-builder"
            element={
              <ProtectedRoute>
                <Layout>
                  <ProgramBuilder />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/clients"
            element={
              <ProtectedRoute>
                <Layout>
                  <Clients />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/clients/:clientId"
            element={
              <ProtectedRoute>
                <Layout>
                  <ClientDetail />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/programs"
            element={
              <ProtectedRoute>
                <Layout>
                  <Programs />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/programs/draft/:programId"
            element={
              <ProtectedRoute>
                <Layout>
                  <ProgramDraftReview />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/programs/:programId"
            element={
              <ProtectedRoute>
                <Layout>
                  <ProgramTemplateView />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/my-programs"
            element={
              <ProtectedRoute>
                <Layout>
                  <MyPrograms />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/my-programs/:assignmentId"
            element={
              <ProtectedRoute>
                <Layout>
                  <ProgramDetails />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
