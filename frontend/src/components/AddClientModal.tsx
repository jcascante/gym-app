import { useState } from 'react';
import { createClient, type CreateClientRequest } from '../services/clients';
import { ApiError } from '../services/api';
import './AddClientModal.css';

interface AddClientModalProps {
  onClose: () => void;
  onClientAdded: () => void;
}

export default function AddClientModal({ onClose, onClientAdded }: AddClientModalProps) {
  const [step, setStep] = useState<'form' | 'checking' | 'result'>('form');
  const [formData, setFormData] = useState<CreateClientRequest>({
    email: '',
    first_name: '',
    last_name: '',
    phone_number: '',
    send_welcome_email: true,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    success: boolean;
    message: string;
    isNew?: boolean;
    alreadyAssigned?: boolean;
  } | null>(null);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    if (!formData.first_name.trim()) {
      newErrors.first_name = 'First name is required';
    }

    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Last name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      setStep('checking');
      setErrors({});

      const response = await createClient(formData);

      // Show result
      setStep('result');

      if (response.is_new) {
        setResult({
          success: true,
          message: `New client ${response.name} has been created and assigned to you!`,
          isNew: true,
        });
      } else if (response.already_assigned) {
        setResult({
          success: true,
          message: `${response.name} is already assigned to you.`,
          isNew: false,
          alreadyAssigned: true,
        });
      } else {
        setResult({
          success: true,
          message: `Existing client ${response.name} has been assigned to you!`,
          isNew: false,
        });
      }
    } catch (err) {
      setStep('result');

      if (err instanceof ApiError) {
        setResult({
          success: false,
          message: err.message,
        });
      } else {
        setResult({
          success: false,
          message: 'Failed to add client. Please try again.',
        });
      }
      console.error('Error adding client:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (result?.success) {
      onClientAdded();
    }
    onClose();
  };

  const handleReset = () => {
    setStep('form');
    setFormData({
      email: '',
      first_name: '',
      last_name: '',
      phone_number: '',
      send_welcome_email: true,
    });
    setResult(null);
    setErrors({});
  };

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add New Client</h2>
          <button className="modal-close" onClick={handleClose}>
            ✕
          </button>
        </div>

        {step === 'form' && (
          <form onSubmit={handleSubmit} className="modal-body">
            <div className="form-section">
              <h3>Client Information</h3>
              <p className="form-hint">
                Enter the client's email to check if they already have an account.
              </p>
            </div>

            <div className="form-group">
              <label htmlFor="email">
                Email <span className="required">*</span>
              </label>
              <input
                type="email"
                id="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                className={errors.email ? 'error' : ''}
                placeholder="client@example.com"
                autoComplete="email"
              />
              {errors.email && <span className="error-message">{errors.email}</span>}
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="first_name">
                  First Name <span className="required">*</span>
                </label>
                <input
                  type="text"
                  id="first_name"
                  value={formData.first_name}
                  onChange={(e) =>
                    setFormData({ ...formData, first_name: e.target.value })
                  }
                  className={errors.first_name ? 'error' : ''}
                  placeholder="John"
                  autoComplete="given-name"
                />
                {errors.first_name && (
                  <span className="error-message">{errors.first_name}</span>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="last_name">
                  Last Name <span className="required">*</span>
                </label>
                <input
                  type="text"
                  id="last_name"
                  value={formData.last_name}
                  onChange={(e) =>
                    setFormData({ ...formData, last_name: e.target.value })
                  }
                  className={errors.last_name ? 'error' : ''}
                  placeholder="Doe"
                  autoComplete="family-name"
                />
                {errors.last_name && (
                  <span className="error-message">{errors.last_name}</span>
                )}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="phone_number">Phone Number (optional)</label>
              <input
                type="tel"
                id="phone_number"
                value={formData.phone_number}
                onChange={(e) =>
                  setFormData({ ...formData, phone_number: e.target.value })
                }
                placeholder="+1234567890"
                autoComplete="tel"
              />
            </div>

            <div className="form-group checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.send_welcome_email}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      send_welcome_email: e.target.checked,
                    })
                  }
                />
                <span>Send welcome email with login credentials</span>
              </label>
              <p className="form-hint">
                If this is a new client, they'll receive an email with their login
                details.
              </p>
            </div>

            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={handleClose}>
                Cancel
              </button>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Adding Client...' : 'Add Client'}
              </button>
            </div>
          </form>
        )}

        {step === 'checking' && (
          <div className="modal-body">
            <div className="loading-state">
              <div className="spinner"></div>
              <h3>Checking client information...</h3>
              <p>Please wait while we process your request.</p>
            </div>
          </div>
        )}

        {step === 'result' && result && (
          <div className="modal-body">
            <div className={`result-state ${result.success ? 'success' : 'error'}`}>
              <div className="result-icon">
                {result.success ? '✅' : '⚠️'}
              </div>
              <h3>{result.success ? 'Success!' : 'Error'}</h3>
              <p>{result.message}</p>

              {result.success && result.isNew && (
                <div className="result-note">
                  {formData.send_welcome_email ? (
                    <p>
                      📧 A welcome email with login credentials has been sent to{' '}
                      <strong>{formData.email}</strong>
                    </p>
                  ) : (
                    <p>
                      Remember to share login credentials with your new client at{' '}
                      <strong>{formData.email}</strong>
                    </p>
                  )}
                </div>
              )}

              <div className="modal-footer">
                {result.success ? (
                  <>
                    <button className="btn-secondary" onClick={handleReset}>
                      Add Another Client
                    </button>
                    <button className="btn-primary" onClick={handleClose}>
                      Done
                    </button>
                  </>
                ) : (
                  <>
                    <button className="btn-secondary" onClick={handleClose}>
                      Cancel
                    </button>
                    <button className="btn-primary" onClick={handleReset}>
                      Try Again
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
