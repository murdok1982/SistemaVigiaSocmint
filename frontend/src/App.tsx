import { lazy, Suspense, useCallback, useEffect, useState } from 'react'
import { BrowserRouter, NavLink, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { FileText, LayoutDashboard, LogOut, Moon, Shield, Sun, Users } from 'lucide-react'
import { Login } from './pages/Login'
import { AuthProvider, useAuth } from './lib/AuthContext'
import { useKeyboardShortcuts } from './lib/useKeyboardShortcuts'
import { useTheme } from './lib/useTheme'
import { getLang, setLang } from './lib/i18n'
import { requestNotificationPermission } from './lib/pushNotifications'
import type { Lang } from './lib/i18n'
import type { ReactNode } from 'react'

const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })))
const AlertDetail = lazy(() => import('./pages/AlertDetail').then(m => ({ default: m.AlertDetail })))
const AuditPage = lazy(() => import('./pages/AuditPage').then(m => ({ default: m.AuditPage })))
const AdminPage = lazy(() => import('./pages/AdminPage').then(m => ({ default: m.AdminPage })))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 2,
    },
  },
})

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: <LayoutDashboard size={18} />, end: true },
  { to: '/audit', label: 'Auditoría', icon: <FileText size={18} />, end: false },
  { to: '/admin', label: 'Administración', icon: <Users size={18} />, end: false },
]

const SUSPENSE_FALLBACK = (
  <div className="flex items-center justify-center min-h-screen bg-slate-900">
    <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
  </div>
)

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AppLayout() {
  const { logout, user } = useAuth()
  const navigate = useNavigate()
  const { theme, toggleTheme } = useTheme()
  const [lang, setLangState] = useState<Lang>(getLang())

  useKeyboardShortcuts({
    'Ctrl+1': () => navigate('/'),
    'Ctrl+2': () => navigate('/audit'),
    'Ctrl+3': () => navigate('/admin'),
  })

  useEffect(() => {
    const handler = () => setLangState(getLang())
    window.addEventListener('vigia-lang-change', handler)
    return () => window.removeEventListener('vigia-lang-change', handler)
  }, [])

  const handleLangChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setLang(e.target.value as Lang)
  }, [])

  return (
    <div className="flex min-h-screen bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100">
      <aside
        className="fixed inset-y-0 left-0 w-56 border-r border-slate-700 bg-slate-900 flex flex-col z-30"
        aria-label="Navegación principal"
      >
        <div className="flex items-center gap-2.5 px-4 py-5 border-b border-slate-700">
          <Shield size={20} className="text-amber-400" aria-hidden="true" />
          <span className="font-semibold text-sm text-slate-100 tracking-wide">VIGÍA Monitor</span>
        </div>

        <nav className="flex-1 px-2 py-4 space-y-1" aria-label="Secciones">
          {NAV_ITEMS.map(({ to, label, icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                [
                  'flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400',
                  isActive
                    ? 'bg-slate-700 text-slate-100'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200',
                ].join(' ')
              }
            >
              <span aria-hidden="true">{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-3 border-t border-slate-700 space-y-2">
          {user && (
            <p className="text-xs text-slate-400 truncate">
              {user.full_name || user.username}
            </p>
          )}
          <select
            value={lang}
            onChange={handleLangChange}
            className="w-full px-2 py-1 bg-slate-900 border border-slate-700 rounded text-xs text-slate-300"
          >
            <option value="es">Español</option>
            <option value="en">English</option>
          </select>
          <button
            onClick={toggleTheme}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-md text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
            {theme === 'dark' ? 'Modo claro' : 'Modo oscuro'}
          </button>
          <button
            onClick={logout}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-md text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
          >
            <LogOut size={16} aria-hidden="true" />
            Cerrar sesión
          </button>
          <p className="text-xs text-slate-500 leading-relaxed">
            Prototipo interno. Revisión humana obligatoria.
          </p>
        </div>
      </aside>

      <div className="flex-1 ml-56 min-w-0">
        <Suspense fallback={SUSPENSE_FALLBACK}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/alerts/:id" element={<AlertDetail />} />
            <Route path="/audit" element={<AuditPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </div>
    </div>
  )
}

function LoginWithNotifications() {
  const { isAuthenticated } = useAuth()
  const [requested, setRequested] = useState(false)

  useEffect(() => {
    if (isAuthenticated && !requested) {
      setRequested(true)
      requestNotificationPermission()
    }
  }, [isAuthenticated, requested])

  return null
}

export default function App() {
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <LoginWithNotifications />
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </AuthProvider>
  )
}
