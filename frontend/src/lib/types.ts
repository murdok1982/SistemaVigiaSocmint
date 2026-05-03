export type RiskLevel = 'VERDE' | 'AMARILLO' | 'NARANJA' | 'ROJO'
export type AlertStatus = 'PENDIENTE' | 'ESCALADA' | 'ARCHIVADA' | 'FALSO_POSITIVO'
export type ReviewAction = 'ESCALAR' | 'ARCHIVAR' | 'FALSO_POSITIVO'

export interface Indicator {
  type: string
  value: string
  explanation: string
  confidence: number
}

export interface Alert {
  id: string
  platform: string
  content_excerpt: string
  content_full: string
  indicators: Indicator[]
  risk_score: number
  risk_level: RiskLevel
  status: AlertStatus
  created_at: string
  reviewed_at: string | null
  reviewed_by: string | null
  analyst_notes: string | null
}

export interface AlertListItem {
  id: string
  platform: string
  content_excerpt: string
  indicators: Indicator[]
  risk_score: number
  risk_level: RiskLevel
  status: AlertStatus
  created_at: string
}

export interface AlertsResponse {
  items: AlertListItem[]
  total: number
  page: number
  page_size: number
}

export interface ReviewRequest {
  action: ReviewAction
  notes: string
  analyst_id: string
}

export interface ReviewResponse {
  success: boolean
  message: string
}

export interface AuditEntry {
  id: string
  timestamp: string
  agent: string
  action_type: string
  target_id: string | null
  details: string
  alert_id: string | null
}

export interface AuditLogResponse {
  items: AuditEntry[]
  total: number
  page: number
  page_size: number
}

export interface SystemStats {
  alerts_today: number
  pending_review: number
  by_level: Record<RiskLevel, number>
  system_status: 'online' | 'degraded' | 'offline'
}

export interface AlertFilters {
  risk_level?: RiskLevel
  platform?: string
  status?: AlertStatus
  page?: number
  page_size?: number
}

export interface AuditFilters {
  date_from?: string
  date_to?: string
  agent?: string
  action_type?: string
  page?: number
  page_size?: number
}

export interface OrchestratorAction {
  step: number
  agent: string
  task: string
  status: string
}

export interface OrchestratorResponse {
  objective: string
  selected_agents: string[]
  reasoning_summary: string
  actions: OrchestratorAction[]
  final_recommendation: string
  requires_human_approval: boolean
  audit_note: string
}

export interface AnalysisRequest {
  objective: string
  platforms?: string
  max_results?: number
}

export interface LoginRequest {
  username: string
  password: string
  mfa_token?: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}
