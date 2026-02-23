import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listMyClients, type ClientSummary } from '../services/clients';
import { ApiError } from '../services/api';
import AddClientModal from '../components/AddClientModal';
import './Clients.css';

export default function Clients() {
  const navigate = useNavigate();
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive' | 'new'>('all');
  const [showAddModal, setShowAddModal] = useState(false);

  // Load clients
  useEffect(() => {
    loadClients();
  }, [statusFilter]);

  const loadClients = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {};
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }

      const response = await listMyClients(params);
      setClients(response.clients);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load clients');
      }
      console.error('Error loading clients:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearSearch = () => {
    setSearchQuery('');
  };

  const handleClientAdded = () => {
    setShowAddModal(false);
    loadClients();  // Reload client list
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'active':
        return 'status-badge status-active';
      case 'new':
        return 'status-badge status-new';
      case 'inactive':
        return 'status-badge status-inactive';
      default:
        return 'status-badge';
    }
  };

  const formatLastWorkout = (lastWorkout?: string) => {
    if (!lastWorkout) return 'No workouts yet';

    const date = new Date(lastWorkout);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return '1 day ago';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
  };

  return (
    <div className="clients-page">
      <div className="clients-header">
        <div className="header-content">
          <h1>My Clients</h1>
          <p>Manage your assigned clients</p>
        </div>
        <button className="btn-primary" onClick={() => setShowAddModal(true)}>
          <span className="button-icon">➕</span>
          Add New Client
        </button>
      </div>

      <div className="clients-controls">
        <div className="search-bar">
          <input
            type="search"
            placeholder="Search by name or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
            autoFocus
          />
          {searchQuery && (
            <button
              type="button"
              className="clear-button"
              onClick={handleClearSearch}
              title="Clear search"
            >
              ✕
            </button>
          )}
        </div>

        <div className="filter-tabs">
          <button
            className={`filter-tab ${statusFilter === 'all' ? 'active' : ''}`}
            onClick={() => setStatusFilter('all')}
          >
            All Clients
          </button>
          <button
            className={`filter-tab ${statusFilter === 'active' ? 'active' : ''}`}
            onClick={() => setStatusFilter('active')}
          >
            Active
          </button>
          <button
            className={`filter-tab ${statusFilter === 'new' ? 'active' : ''}`}
            onClick={() => setStatusFilter('new')}
          >
            New
          </button>
          <button
            className={`filter-tab ${statusFilter === 'inactive' ? 'active' : ''}`}
            onClick={() => setStatusFilter('inactive')}
          >
            Inactive
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading clients...</p>
        </div>
      ) : (() => {
        // Apply instant filtering based on search query
        const filtered = searchQuery.trim()
          ? clients.filter(c => c.name.toLowerCase().includes(searchQuery.toLowerCase()) || c.email.toLowerCase().includes(searchQuery.toLowerCase()))
          : clients;

        return filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">👥</div>
            <h2>No clients found</h2>
            <p>
              {searchQuery
                ? `No clients match "${searchQuery}".`
                : statusFilter !== 'all'
                  ? `No ${statusFilter} clients. Try changing the filter.`
                  : 'Get started by adding your first client!'}
            </p>
            {statusFilter === 'all' && !searchQuery && (
              <button className="btn-primary" onClick={() => setShowAddModal(true)}>
                <span className="button-icon">➕</span>
                Add Your First Client
              </button>
            )}
          </div>
        ) : (
          <>
            <div className="clients-count">
              Showing {filtered.length} client{filtered.length !== 1 ? 's' : ''}
            </div>

            <div className="clients-grid">
              {filtered.map((client) => (
              <div
                key={client.id}
                className="client-card"
                onClick={() => navigate(`/clients/${client.id}`)}
              >
                <div className="client-card-header">
                  <div className="client-avatar">
                    {client.profile_photo ? (
                      <img src={client.profile_photo} alt={client.name} />
                    ) : (
                      <div className="avatar-placeholder">
                        {client.first_name[0]}
                        {client.last_name[0]}
                      </div>
                    )}
                  </div>
                  <div className="client-info">
                    <h3>{client.name}</h3>
                    <p className="client-email">{client.email}</p>
                  </div>
                  <span className={getStatusBadgeClass(client.status)}>
                    {client.status}
                  </span>
                </div>

                <div className="client-card-stats">
                  <div className="stat">
                    <span className="stat-icon">📊</span>
                    <div className="stat-content">
                      <span className="stat-value">{client.active_programs}</span>
                      <span className="stat-label">Active Programs</span>
                    </div>
                  </div>

                  <div className="stat">
                    <span className="stat-icon">🏋️</span>
                    <div className="stat-content">
                      <span className="stat-value">
                        {formatLastWorkout(client.last_workout)}
                      </span>
                      <span className="stat-label">Last Workout</span>
                    </div>
                  </div>
                </div>

                <div className="client-card-footer">
                  <div className="profile-indicators">
                    {client.profile_complete ? (
                      <span className="indicator complete">
                        ✓ Profile Complete
                      </span>
                    ) : (
                      <span className="indicator incomplete">
                        ⚠️ Profile Incomplete
                      </span>
                    )}
                    {client.has_one_rep_maxes && (
                      <span className="indicator">💪 Has 1RMs</span>
                    )}
                  </div>
                  <button
                    className="btn-secondary btn-sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/program-builder?clientId=${client.id}`);
                    }}
                  >
                    Build Program →
                  </button>
                </div>
              </div>
            ))}
            </div>
          </>
        );
      })()}

      {showAddModal && (
        <AddClientModal
          onClose={() => setShowAddModal(false)}
          onClientAdded={handleClientAdded}
        />
      )}
    </div>
  );
}
