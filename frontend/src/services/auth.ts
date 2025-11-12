/**
 * Authentication API service
 */

import { apiFetch } from './api';
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  User,
} from '../types/user';

/**
 * Login with username/email and password
 *
 * @param username - Username or email address
 * @param password - User password
 * @returns Promise with access token and user data
 */
export async function login(username: string, password: string): Promise<LoginResponse> {
  // FastAPI OAuth2PasswordRequestForm expects form data, not JSON
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await fetch(
    `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/auth/login`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    }
  );

  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    throw new Error(errorData.detail || `Login failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Register a new user account
 *
 * @param data - Registration data (email, username, password, optional full_name)
 * @returns Promise with created user data
 */
export async function register(data: RegisterRequest): Promise<RegisterResponse> {
  return apiFetch<RegisterResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Get current authenticated user's profile
 *
 * @returns Promise with user data
 */
export async function getCurrentUser(): Promise<User> {
  return apiFetch<User>('/auth/me');
}

/**
 * Test authentication endpoint (development only)
 *
 * @returns Promise with test message
 */
export async function testAuth(): Promise<{ message: string }> {
  return apiFetch<{ message: string }>('/auth/test-auth');
}
