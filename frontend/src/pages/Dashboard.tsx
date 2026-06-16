import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { AlertFilters } from '@/lib/types'
import { AlertQueue } from '@/components/AlertQueue'
import { RunAnalysisModal } from '@/components/RunAnalysisModal'
import { StatsBar } from '@/components/StatsBar'
import { Play, Download, Map, Network, FileText, Menu, X, Search } from 'lucide-react'
import { MapView } from '@/components/MapView'
import { NetworkGraph } from '@/components/NetworkGraph'
import { ReportGenerator } from '@/components/ReportGenerator'

const VIEWS = [
  { key: 'queue' as const, label: 'Cola de Alertas', icon: FileText },
  { key: 'map' as const, label: 'Mapa Táctico', icon: Map },
  { key: 'network' as const, label: 'Grafos de Red', icon: Network },
  { key: 'reports' as const, label: 'Informes', icon: FileText },
]

export function Dashboard() {
  const [filters, setFilters] = useState<AlertFilters>({ page: 1, page_size: 20 })
  const [showAnalysisModal, setShowAnalysisModal] = useState(false)
  const [activeView, setActiveView] = useState<'queue' | 'map' | 'network' | 'reports'>('queue')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 30_000,
  })

  const { data: alertsData, isLoading: alertsLoading, isError: alertsError, refetch: refetchAlerts } = useQuery({
    queryKey: ['alerts', filters],
    queryFn: () => api.getAlerts(filters),
    refetchInterval: 60_000,
  })

  const filteredAlerts = useMemo(() => {
    const items = alertsData?.items ?? []
    if (!searchQuery.trim()) return items
    const q = searchQuery.toLowerCase()
    return items.filter((a) => a.content_excerpt.toLowerCase().includes(q))
  }, [alertsData?.items, searchQuery])

  return (
    <main className="p-4 md:p-6 space-y-4 md:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Centro de Monitoreo Táctico</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Sistema VIGÍA — Nivel: ESTATAL-MILITAR — Revisión humana obligatoria
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAnalysisModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-md bg-amber-600 text-sm font-semibold text-white hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-400"
          >
            <Play size={15} aria-hidden="true" />
            <span className="hidden sm:inline">Lanzar Análisis</span>
          </button>
          <button
            onClick={() => {/* Export to STIX */}}
            className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-md bg-slate-700 text-sm font-semibold text-slate-100 hover:bg-slate-600 transition-colors"
          >
            <Download size={15} />
            Exportar
          </button>
        </div>
      </div>

      <div className="overflow-x-auto -mx-4 px-4 md:mx-0 md:px-0">
        <div className="min-w-[640px] md:min-w-0">
          <StatsBar stats={stats} isLoading={statsLoading} />
        </div>
      </div>

      <div className="md:hidden flex items-center justify-between">
        <div className="flex gap-1 overflow-x-auto pb-1 scrollbar-none">
          {VIEWS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveView(key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md whitespace-nowrap transition-colors ${
                activeView === key
                  ? 'bg-amber-600/20 text-amber-400 border border-amber-500/40'
                  : 'text-slate-400 hover:text-slate-200 bg-slate-800 border border-slate-700'
              }`}
            >
              <Icon size={14} />
              {label}
            </button>
          ))}
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors md:hidden"
          aria-label="Menú de navegación"
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
        </button>
      </div>

      <div className="hidden md:flex gap-2 border-b border-slate-700">
        {VIEWS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveView(key)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeView === key
                ? 'border-amber-500 text-amber-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {activeView === 'queue' && (
        <>
          <div className="relative max-w-md">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar alertas por contenido..."
              className="w-full pl-9 pr-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
            />
          </div>
          <AlertQueue
            alerts={filteredAlerts}
            isLoading={alertsLoading}
            isError={alertsError}
            filters={filters}
            onFiltersChange={setFilters}
            total={searchQuery.trim() ? filteredAlerts.length : (alertsData?.total ?? 0)}
            page={filters.page ?? 1}
            pageSize={filters.page_size ?? 20}
            onPageChange={(p) => setFilters((f) => ({ ...f, page: p }))}
            onRetry={() => refetchAlerts()}
            onLaunchAnalysis={() => setShowAnalysisModal(true)}
          />
        </>
      )}

      {activeView === 'map' && <MapView alerts={alertsData?.items ?? []} />}
      {activeView === 'network' && <NetworkGraph alerts={alertsData?.items ?? []} />}
      {activeView === 'reports' && <ReportGenerator />}

      {showAnalysisModal && (
        <RunAnalysisModal onClose={() => setShowAnalysisModal(false)} />
      )}
    </main>
  )
}
