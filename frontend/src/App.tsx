import { BrowserRouter, NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { FileText, LayoutDashboard, Shield } from 'lucide-react'
import { Dashboard } from './pages/Dashboard'
import { AlertDetail } from './pages/AlertDetail'
import { AuditPage } from './pages/AuditPage'

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
]

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="flex min-h-screen bg-slate-900 text-slate-100">
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

            <div className="px-4 py-3 border-t border-slate-700">
              <p className="text-xs text-slate-500 leading-relaxed">
                Prototipo interno. Revisión humana obligatoria.
              </p>
            </div>
          </aside>

          <div className="flex-1 ml-56 min-w-0">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/alerts/:id" element={<AlertDetail />} />
              <Route path="/audit" element={<AuditPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
