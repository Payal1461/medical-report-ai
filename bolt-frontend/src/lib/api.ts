import type {
  AuthResponse,
  ReportListItem,
  ReportSummary,
  TrendResponse,
  UploadResponse,
  User,
} from '@/types';

const BASE_URL = 'http://localhost:8000';

function getToken(): string | null {
  return localStorage.getItem('medinsight_token');
}

export function setToken(token: string): void {
  localStorage.setItem('medinsight_token', token);
}

export function clearToken(): void {
  localStorage.removeItem('medinsight_token');
}

export function hasToken(): boolean {
  return !!getToken();
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  ...authHeader(),
  };

  if (options.body instanceof FormData) {
    delete headers['Content-Type'];
  } else if (options.body) {
    headers['Content-Type'] = 'application/json';
  }

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  } catch {
    throw new Error('Cannot reach the server. Make sure the backend is running.');
  }

  let data: unknown;
  const text = await res.text();
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!res.ok) {
    const detail =
      data && typeof data === 'object' && 'detail' in data
        ? String((data as { detail: unknown }).detail)
        : typeof data === 'string' && data
          ? data
          : `Request failed (${res.status})`;
    throw new Error(detail);
  }

  return data as T;
}

export function authHeader(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const api = {
  signup: (name: string, email: string, password: string) =>
    request<AuthResponse>('/signup', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>('/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<User>('/me', { method: 'GET' }),

  upload: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return request<UploadResponse>('/upload', {
      method: 'POST',
      body: form,
    });
  },

  reports: () => request<ReportListItem[]>('/reports', { method: 'GET' }),

  report: (id: number) =>
    request<ReportListItem>(`/report/${id}`, { method: 'GET' }),

  dashboard: (reportId: number) =>
    request<ReportSummary>(`/dashboard/${reportId}`, { method: 'GET' }),

  trends: (name: string) =>
    request<TrendResponse>(
      `/trends/${encodeURIComponent(name)}`,
      { method: 'GET' },
    ),
};
