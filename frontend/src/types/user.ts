/**
 * User type definitions matching backend Pydantic schemas
 * Updated for multi-tenant role-based system
 */

export const UserRole = {
  APPLICATION_SUPPORT: 'APPLICATION_SUPPORT',
  SUBSCRIPTION_ADMIN: 'SUBSCRIPTION_ADMIN',
  COACH: 'COACH',
  CLIENT: 'CLIENT',
} as const;

export type UserRole = typeof UserRole[keyof typeof UserRole];

export interface UserProfile {
  name?: string;
  phone?: string;
  bio?: string;
  avatar?: string;
  age?: number;
  goals?: string[];
  certifications?: string[];
  [key: string]: any; // Allow additional profile fields
}

export interface User {
  id: string; // UUID
  subscription_id: string | null; // UUID or null for APPLICATION_SUPPORT
  location_id: string | null; // UUID or null
  role: UserRole;
  email: string;
  profile: UserProfile | null;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
  password_must_be_changed: boolean;
}

export interface RegisterRequest {
  email: string;
  password: string;
  role: UserRole;
  subscription_id?: string;
  location_id?: string;
  profile?: UserProfile;
}

export interface RegisterResponse extends User {}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ChangePasswordResponse {
  message: string;
  detail?: string;
}

export interface UserListResponse {
  users: User[];
  total: number;
  skip: number;
  limit: number;
}

// Helper functions
export function getUserDisplayName(user: User | null): string {
  if (!user) return 'Guest';
  return user.profile?.name || user.email.split('@')[0];
}

export function isAdmin(user: User | null): boolean {
  return user?.role === UserRole.SUBSCRIPTION_ADMIN ||
         user?.role === UserRole.APPLICATION_SUPPORT;
}

export function isSupport(user: User | null): boolean {
  return user?.role === UserRole.APPLICATION_SUPPORT;
}

export function isCoach(user: User | null): boolean {
  return user?.role === UserRole.COACH;
}

export function isClient(user: User | null): boolean {
  return user?.role === UserRole.CLIENT;
}
