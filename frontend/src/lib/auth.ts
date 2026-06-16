/**
 * Auth helpers — VIGÍA v2.1
 *
 * Reglas críticas:
 *  - getAccessToken() lee localStorage en CADA invocación.
 *    NUNCA cachear el token en el módulo (bug histórico de la auditoría WAVE 1).
 *  - login()/logout() emiten un CustomEvent('vigia-auth-change')
 *    para que AuthContext (y otros listeners) reaccionen sin recargar la página.
 */

const ACCESS_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'

export const AUTH_EVENT = 'vigia-auth-change'

const BASE_URL =
  (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'

export interface LoginCredentials {
  username: string
  password: string
  mfa_token?: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

/** Error específico para distinguir el caso de MFA requerido. */
export class MfaRequiredError extends Error {
  constructor(message = 'Token MFA requerido') {
    super(message)
    this.name = 'MfaRequiredError'
  }
}

/** Lectura DINÁMICA del access token. No cachear nunca a nivel de módulo. */
export function getAccessToken(): string | null {
  try {
    return localStorage.getItem(ACCESS_KEY)
  } catch {
    return null
  }
}

export function getRefreshToken(): string | null {
  try {
    return localStorage.getItem(REFRESH_KEY)
  } catch {
    return null
  }
}

export function setAccessToken(token: string): void {
  localStorage.setItem(ACCESS_KEY, token)
  emitAuthChange()
}

export function setRefreshToken(token: string): void {
  localStorage.setItem(REFRESH_KEY, token)
}

export function setTokens(tokens: Pick<AuthTokens, 'access_token' | 'refresh_token'>): void {
  localStorage.setItem(ACCESS_KEY, tokens.access_token)
  localStorage.setItem(REFRESH_KEY, tokens.refresh_token)
  emitAuthChange()
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
  emitAuthChange()
}

function emitAuthChange(): void {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(AUTH_EVENT))
}

/**
 * login() habla directamente con el backend (NO usa el wrapper api.ts para
 * evitar dependencia circular: api.ts depende de auth para los interceptors).
 */
export async function login(credentials: LoginCredentials): Promise<AuthTokens> {
  const response = await fetch(`${BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  })

  if (!response.ok) {
    const text = await response.text()
    let detail = `Error ${response.status}`
    try {
      const parsed = JSON.parse(text) as { detail?: string; code?: string }
      detail = parsed.detail ?? detail
      if (
        response.status === 401 &&
        (detail.toLowerCase().includes('mfa') || parsed.code === 'mfa_required')
      ) {
        throw new MfaRequiredError(detail)
      }
    } catch (err) {
      if (err instanceof MfaRequiredError) throw err
      // si el body no es JSON ignoramos
    }
    throw new Error(detail)
  }

  const tokens = (await response.json()) as AuthTokens
  setTokens({
    access_token: tokens.access_token,
    refresh_token: tokens.refresh_token,
  })
  return tokens
}

/**
 * logout() — intenta invalidar el refresh en el servidor y SIEMPRE limpia local.
 * Nunca lanza: aunque el backend falle, el usuario debe quedar deslogueado en cliente.
 */
export async function logout(): Promise<void> {
  const refresh = getRefreshToken()
  const access = getAccessToken()
  try {
    if (refresh) {
      await fetch(`${BASE_URL}/api/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(access ? { Authorization: `Bearer ${access}` } : {}),
        },
        body: JSON.stringify({ refresh_token: refresh }),
        // si tarda demasiado, no bloqueamos al usuario
        keepalive: true,
      })
    }
  } catch {
    // ignorar — limpiamos local de todas formas
  } finally {
    clearTokens()
  }
}

/**
 * Llama al endpoint /auth/refresh y persiste los nuevos tokens.
 * Devuelve null si el refresh falla — el caller debe llamar logout().
 */
export async function refreshAccessToken(): Promise<AuthTokens | null> {
  const refresh = getRefreshToken()
  if (!refresh) return null
  try {
    const response = await fetch(`${BASE_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    })
    if (!response.ok) return null
    const tokens = (await response.json()) as AuthTokens
    setTokens({
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token,
    })
    return tokens
  } catch {
    return null
  }
}

export function isAuthenticated(): boolean {
  return Boolean(getAccessToken())
}
