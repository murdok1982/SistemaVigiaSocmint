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
import { clearTokens, getAccessToken, refreshAccessToken } from './auth'

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'
const API_KEY = (import.meta.env.VITE_API_KEY as string | undefined) ?? ''

/**
 * Coordina refrescos de token concurrentes — si dos requests reciben 401 a la vez,
 * sólo una llama al endpoint /refresh y el resto espera al mismo Promise.
 */
let refreshInFlight: Promise<boolean> | null = null

async function ensureFreshToken(): Promise<boolean> {
  if (refreshInFlight) return refreshInFlight
  refreshInFlight = (async () => {
    const tokens = await refreshAccessToken()
    return tokens !== null
  })()
  try {
    return await refreshInFlight
  } finally {
    refreshInFlight = null
  }
}

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: BodyInit | null
  /** Si true, no se intentará refresh ni se incluirán headers Auth (para /auth/login y /auth/refresh). */
  skipAuth?: boolean
  /** AbortSignal para cancelación (compatible con react-query). */
  signal?: AbortSignal
  /** Si true, devuelve la Response cruda en vez de parsear JSON (para descargar Blobs). */
  raw?: boolean
}

interface ApiErrorBody {
  detail?: string
  code?: string
}

export class ApiError extends Error {
  readonly status: number
  readonly code?: string

  constructor(message: string, status: number, code?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

async function readErrorBody(response: Response): Promise<ApiErrorBody> {
  try {
    const text = await response.text()
    if (!text) return {}
    return JSON.parse(text) as ApiErrorBody
  } catch {
    return {}
  }
}

function buildHeaders(
  extra: HeadersInit | undefined,
  skipAuth: boolean,
  hasJsonBody: boolean,
): Headers {
  const headers = new Headers(extra)
  if (hasJsonBody && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  if (skipAuth) return headers

  const token = getAccessToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  } else if (API_KEY) {
    headers.set('X-API-Key', API_KEY)
  }
  return headers
}

function redirectToLogin(): void {
  if (typeof window === 'undefined') return
  // Sólo redirigimos si no estamos ya en /login para no loop.
  if (!window.location.pathname.startsWith('/login')) {
    window.location.assign('/login')
  }
}

/**
 * Wrapper fetch con "interceptor" manual:
 *   - inyecta Authorization dinámicamente
 *   - si recibe 401 con code 'token_expired' (o 401 genérico), intenta /auth/refresh UNA vez
 *   - si refresh falla → clearTokens + redirige a /login
 *   - soporta AbortSignal y raw responses (para PDFs/Blobs)
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = `${BASE_URL}${path}`
  const skipAuth = options.skipAuth ?? path.startsWith('/api/auth/')
  const hasJsonBody = typeof options.body === 'string'

  const doFetch = async (): Promise<Response> => {
    const headers = buildHeaders(options.headers, skipAuth, hasJsonBody)
    return fetch(url, {
      method: options.method,
      body: options.body,
      headers,
      signal: options.signal,
      credentials: options.credentials,
      mode: options.mode,
      cache: options.cache,
    })
  }

  let response = await doFetch()

  if (response.status === 401 && !skipAuth) {
    const errBody = await readErrorBody(response.clone())
    const expired = errBody.code === 'token_expired' || !errBody.code
    if (expired) {
      const refreshed = await ensureFreshToken()
      if (refreshed) {
        // Reintentamos la petición original UNA vez con el nuevo token.
        response = await doFetch()
      } else {
        clearTokens()
        redirectToLogin()
        throw new ApiError('Sesión expirada', 401, 'token_expired')
      }
    }
  }

  if (!response.ok) {
    const body = await readErrorBody(response)
    throw new ApiError(
      body.detail ?? `Error ${response.status}`,
      response.status,
      body.code,
    )
  }

  if (options.raw) {
    return response as unknown as T
  }

  // Permitir respuestas vacías (204).
  if (response.status === 204) {
    return undefined as unknown as T
  }

  return response.json() as Promise<T>
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined)
  if (entries.length === 0) return ''
  return '?' + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString()
}

export interface ReportPeriodRequest {
  date_from: string
  date_to: string
  classification?: string
  recipient_pgp_pubkey?: string
}

export const api = {
  // Auth — login y refresh viven en src/lib/auth.ts.
  // Mantenemos atajos para compatibilidad con código existente.
  login(credentials: LoginRequest): Promise<LoginResponse> {
    return request<LoginResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
      skipAuth: true,
    })
  },

  refreshToken(refreshToken: string): Promise<LoginResponse> {
    return request<LoginResponse>('/api/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
      skipAuth: true,
    })
  },

  // Alerts
  getAlerts(filters: AlertFilters = {}, signal?: AbortSignal): Promise<AlertsResponse> {
    const query = buildQuery({
      risk_level: filters.risk_level,
      platform: filters.platform,
      status: filters.status,
      page: filters.page ?? 1,
      page_size: filters.page_size ?? 20,
    })
    return request<AlertsResponse>(`/api/alerts${query}`, { signal })
  },

  getAlert(id: string, signal?: AbortSignal): Promise<Alert> {
    return request<Alert>(`/api/alerts/${id}`, { signal })
  },

  reviewAlert(id: string, body: ReviewRequest): Promise<ReviewResponse> {
    return request<ReviewResponse>(`/api/alerts/${id}/review`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },

  // Audit
  getAuditLog(filters: AuditFilters = {}, signal?: AbortSignal): Promise<AuditLogResponse> {
    const query = buildQuery({
      date_from: filters.date_from,
      date_to: filters.date_to,
      agent: filters.agent,
      action_type: filters.action_type,
      page: filters.page ?? 1,
      page_size: filters.page_size ?? 50,
    })
    return request<AuditLogResponse>(`/api/audit-log${query}`, { signal })
  },

  // System
  getHealth(signal?: AbortSignal): Promise<SystemStats> {
    return request<SystemStats>('/api/health', { signal })
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
  createAnalyst(data: {
    username: string
    email: string
    full_name: string
    password: string
    role?: string
    clearance_level?: string
  }): Promise<{ message: string; analyst_id: string }> {
    return request<{ message: string; analyst_id: string }>('/api/analysts', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  // Reports — PDF (response binaria)
  async generateReport(body: ReportPeriodRequest, signal?: AbortSignal): Promise<Blob> {
    const response = await request<Response>('/api/reports/period', {
      method: 'POST',
      body: JSON.stringify(body),
      raw: true,
      signal,
      headers: { Accept: 'application/pdf' },
    })
    return response.blob()
  },

  // Export STIX — endpoint asumido por contrato con backend
  async exportStix(ids: string[], signal?: AbortSignal): Promise<Blob> {
    const query = ids.length ? `?ids=${encodeURIComponent(ids.join(','))}` : ''
    const response = await request<Response>(`/api/alerts/export.stix${query}`, {
      raw: true,
      signal,
      headers: { Accept: 'application/json' },
    })
    return response.blob()
  },
}

export type { LoginRequest, LoginResponse }
