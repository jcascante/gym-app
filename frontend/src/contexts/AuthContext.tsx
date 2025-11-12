import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { login as apiLogin, register as apiRegister, getCurrentUser } from '../services/auth';
import { setToken, removeToken, getToken } from '../services/api';
import type { User, RegisterRequest } from '../types/user';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Check if user is already logged in on mount
  useEffect(() => {
    const initAuth = async () => {
      const token = getToken();

      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        // Verify token is still valid by fetching user data
        const userData = await getCurrentUser();
        setUser(userData);
      } catch (error) {
        // Token is invalid or expired, clear it
        console.error('Failed to restore session:', error);
        removeToken();
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (username: string, password: string): Promise<void> => {
    try {
      const response = await apiLogin(username, password);

      // Store token
      setToken(response.access_token);

      // Set user data
      setUser(response.user);
    } catch (error) {
      // Re-throw error for component to handle
      throw error;
    }
  };

  const register = async (data: RegisterRequest): Promise<void> => {
    try {
      await apiRegister(data);

      // After registration, automatically log in
      await login(data.username, data.password);
    } catch (error) {
      // Re-throw error for component to handle
      throw error;
    }
  };

  const logout = () => {
    removeToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
