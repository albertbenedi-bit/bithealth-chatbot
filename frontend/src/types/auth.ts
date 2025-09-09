import { User } from './api';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}

export interface AuthContextType {
  authState: AuthState;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

export type AuthProvider = 'google-workspace' | 'entra' | 'aws-cognito' | 'internal';

export interface AuthConfig {
  provider: AuthProvider;
  clientId?: string;
  redirectUri?: string;
  scopes?: string[];
}
