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
} from './types'

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'
// VITE_API_KEY se configura en .env.local (nunca commitear el valor real)
const API_KEY = (import.meta.env.VITE_API_KEY as string | undefined) ?? ''

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`

  // Añadir X-API-Key en todas las peticiones de escritura (POST/PUT/DELETE)
  const isWriteMethod = options?.method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method.toUpperCase())
  const authHeaders: Record<string, string> = isWriteMethod && API_KEY ? { 'X-API-Key': API_KEY } : {}

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders,
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    // No exponer el body completo del error al usuario final — solo el status
    const body = await response.text()
    let userMessage: string
    try {
      const parsed = JSON.parse(body) as { detail?: string }
      // Usar detail de FastAPI si existe, sin stack traces
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
}
