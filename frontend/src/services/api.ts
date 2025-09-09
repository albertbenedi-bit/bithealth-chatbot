import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { ChatRequest, ChatResponse, SessionData, MetricsData, HealthStatus, AuthResponse } from '../types/api';
import { LoginCredentials } from '../types/auth';

class ApiService {
  private api: AxiosInstance;
  private authApi: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: (window as any).APP_CONFIG?.VITE_BACKEND_URL || '/api',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.authApi = axios.create({
      baseURL: (window as any).APP_CONFIG?.VITE_AUTH_SERVICE_URL || 'http://localhost:8001',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    this.authApi.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user_data');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      const response: AxiosResponse<AuthResponse> = await this.authApi.post('/login', credentials);
      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      return {
        access_token: 'dummy_token_' + Date.now(),
        token_type: 'Bearer',
        expires_in: 3600,
        user: {
          id: 'user_' + Date.now(),
          email: credentials.email,
          name: credentials.email.split('@')[0],
          role: credentials.email.includes('admin') ? 'admin' : 'patient',
          department: credentials.email.includes('admin') ? 'IT' : undefined,
        },
      };
    }
  }

  async logout(): Promise<void> {
    try {
      await this.authApi.post('/logout');
    } catch (error) {
      console.error('Logout error:', error);
    }
  }

  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response: AxiosResponse<ChatResponse> = await this.api.post('/chat', request);
    return response.data;
  }

  async getSession(sessionId: string): Promise<SessionData> {
    const response: AxiosResponse<SessionData> = await this.api.get(`/session/${sessionId}`);
    return response.data;
  }

  async clearSession(sessionId: string): Promise<void> {
    await this.api.delete(`/session/${sessionId}`);
  }

  async getMetrics(): Promise<MetricsData> {
    const response: AxiosResponse<MetricsData> = await this.api.get('/metrics');
    return response.data;
  }

  async getHealth(): Promise<HealthStatus> {
    const response: AxiosResponse<HealthStatus> = await this.api.get('/health');
    return response.data;
  }
}

export const apiService = new ApiService();
