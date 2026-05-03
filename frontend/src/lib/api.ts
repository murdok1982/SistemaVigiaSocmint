import type {
  Alert,
  AlertFilters,
  AlertsResponse,
  AnalysisRequest,
  AuditFilters,
  AuditLogResponse,
  OrchestratorResponse,
  ReviewRequest,
  ReviewResponse,
  SystemStats,
  LoginRequest,
  LoginResponse,
} from './types'

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'
const API_KEY = (import.meta.env.VITE_API_KEY as string | undefined) ?? ''
const JWT_TOKEN = localStorage.getItem('access_token') ?? ''

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options?.headers as Record<string, string>,
  }

  // Añadir JWT token si está disponible
  if (JWT_TOKEN && !path.includes('/auth/')) {
    headers['Authorization'] = `Bearer ${JWT_TOKEN}`
  } else if (!path.includes('/auth/') && API_KEY) {
    headers['X-API-Key'] = API_KEY
  }

  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const body = await response.text()
    let userMessage: string
    try {
      const parsed = JSON.parse(body) as { detail?: string }
      userMessage = parsed.detail ?? `Error ${response.status}`
    } catch {
      userMessage = `Error ${response.status}`
    }
    throw new Error(userMessage)
  }

  return response.json() as Promise<T>
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined)
  if (entries.length === 0) return ''
  return '?' + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString()
}

export const api = {
  // Auth
  login(credentials: LoginRequest): Promise<LoginResponse> {
    return request<LoginResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    })
  },

  refreshToken(refreshToken: string): Promise<LoginResponse> {
    return request<LoginResponse>('/api/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
  },

  // Alerts
  getAlerts(filters: AlertFilters = {}): Promise<AlertsResponse> {
    const query = buildQuery({
      risk_level: filters.risk_level,
      platform: filters.platform,
      status: filters.status,
      page: filters.page ?? 1,
      page_size: filters.page_size ?? 20,
    })
    return request<AlertsResponse>(`/api/alerts${query}`)
  },

  getAlert(id: string): Promise<Alert> {
    return request<Alert>(`/api/alerts/${id}`)
  },

  reviewAlert(id: string, body: ReviewRequest): Promise<ReviewResponse> {
    return request<ReviewResponse>(`/api/alerts/${id}/review`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },

  // Audit
  getAuditLog(filters: AuditFilters = {}): Promise<AuditLogResponse> {
    const query = buildQuery({
      date_from: filters.date_from,
      date_to: filters.date_to,
      agent: filters.agent,
      action_type: filters.action_type,
      page: filters.page ?? 1,
      page_size: filters.page_size ?? 50,
    })
    return request<AuditLogResponse>(`/api/audit-log${query}`)
  },

  // System
  getHealth(): Promise<SystemStats> {
    return request<SystemStats>('/api/health')
  },

  runAnalysis(params: AnalysisRequest): Promise<OrchestratorResponse> {
    const query = buildQuery({
      objective: params.objective,
      platforms: params.platforms,
      max_results: params.max_results,
    })
    return request<OrchestratorResponse>(`/api/analyze${query}`, { method: 'POST' })
  },

  // Analysts (Admin)
  createAnalyst(data: { username: string; email: string; full_name: string; password: string; role?: string }): Promise<{ message: string; analyst_id: string }> {
    return request<{ message: string; analyst_id: string }>('/api/analysts', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
}

// Export types for convenience
export type { LoginRequest, LoginResponse }
