import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { jwtDecode } from 'jwt-decode'
import {
  AUTH_EVENT,
  type LoginCredentials,
  getAccessToken,
  login as authLogin,
  logout as authLogout,
} from './auth'

export interface AuthUser {
  sub: string
  username: string
  role?: string
  email?: string
  full_name?: string
  exp?: number
}

interface JwtPayload {
  sub?: string
  username?: string
  role?: string
  email?: string
  full_name?: string
  exp?: number
}

interface AuthContextValue {
  isAuthenticated: boolean
  user: AuthUser | null
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function decodeUser(token: string | null): AuthUser | null {
  if (!token) return null
  try {
    const payload = jwtDecode<JwtPayload>(token)
    if (payload.exp && payload.exp * 1000 < Date.now()) {
      // token expirado — el interceptor se encargará del refresh; aquí no marcamos user.
      return null
    }
    return {
      sub: payload.sub ?? '',
      username: payload.username ?? payload.sub ?? 'desconocido',
      role: payload.role,
      email: payload.email,
      full_name: payload.full_name,
      exp: payload.exp,
    }
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => decodeUser(getAccessToken()))

  // Sincronizar con cambios de token (login/logout/refresh) y entre pestañas.
  useEffect(() => {
    function syncFromStorage(): void {
      setUser(decodeUser(getAccessToken()))
    }
    window.addEventListener(AUTH_EVENT, syncFromStorage)
    window.addEventListener('storage', syncFromStorage)
    return () => {
      window.removeEventListener(AUTH_EVENT, syncFromStorage)
      window.removeEventListener('storage', syncFromStorage)
    }
  }, [])

  const login = useCallback(async (credentials: LoginCredentials) => {
    await authLogin(credentials)
    setUser(decodeUser(getAccessToken()))
  }, [])

  const logout = useCallback(async () => {
    await authLogout()
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: Boolean(user),
      user,
      login,
      logout,
    }),
    [user, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth debe usarse dentro de <AuthProvider>')
  }
  return ctx
}
