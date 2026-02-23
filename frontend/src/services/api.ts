/**
 * Base API configuration and utilities
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Get stored JWT token from localStorage
 */
export function getToken(): string | null {
  const token = localStorage.getItem('gym-app-token');
  // Normalize invalid stored values (string "null" or "undefined") to actual null
  if (!token || token === 'null' || token === 'undefined') return null;
  return token;
}

/**
 * Store JWT token in localStorage
 */
export function setToken(token: string): void {
  localStorage.setItem('gym-app-token', token);
}

/**
 * Remove JWT token from localStorage
 */
export function removeToken(): void {
  localStorage.removeItem('gym-app-token');
}

/**
 * Base fetch wrapper with authentication and error handling
 */
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = getToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add Authorization header if token exists
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);

    // Handle non-OK responses
    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { detail: response.statusText };
      }

      const errorMessage = errorData.detail || `HTTP ${response.status}: ${response.statusText}`;
      throw new ApiError(errorMessage, response.status, errorData);
    }

    // Parse JSON response
    const data = await response.json();
    return data as T;
  } catch (error) {
    // Re-throw ApiError as-is
    if (error instanceof ApiError) {
      throw error;
    }

    // Wrap network errors
    if (error instanceof TypeError) {
      throw new ApiError('Network error: Unable to reach the server', 0);
    }

    // Wrap other errors
    throw new ApiError(
      error instanceof Error ? error.message : 'An unknown error occurred',
      0
    );
  }
}
