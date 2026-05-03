import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { AlertFilters, Alert, SystemStats } from '@/lib/types'
import { AlertQueue } from '@/components/AlertQueue'
import { RunAnalysisModal } from '@/components/RunAnalysisModal'
import { StatsBar } from '@/components/StatsBar'
import { Play, Download, Map, Network, FileText } from 'lucide-react'
import { MapView } from '@/components/MapView'
import { NetworkGraph } from '@/components/NetworkGraph'
import { ReportGenerator } from '@/components/ReportGenerator'

export function Dashboard() {
  const [filters, setFilters] = useState<AlertFilters>({ page: 1, page_size: 20 })
  const [showAnalysisModal, setShowAnalysisModal] = useState(false)
  const [activeView, setActiveView] = useState<'queue' | 'map' | 'network' | 'reports'>('queue')
  const queryClient = useQueryClient()

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 30_000,
  })

  const { data: alertsData, isLoading: alertsLoading, isError: alertsError } = useQuery({
    queryKey: ['alerts', filters],
    queryFn: () => api.getAlerts(filters),
    refetchInterval: 60_000,
  })

  return (
    <main className="p-6 space-y-6">
      <div className="flex items-center justify-between">
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
            Lanzar Análisis
          </button>
          <button
            onClick={() => {/* Export to STIX */}}
            className="flex items-center gap-2 px-4 py-2 rounded-md bg-slate-700 text-sm font-semibold text-slate-100 hover:bg-slate-600 transition-colors"
          >
            <Download size={15} />
            Exportar
          </button>
        </div>
      </div>

      <StatsBar stats={stats} isLoading={statsLoading} />

      {/* Selector de vista */}
      <div className="flex gap-2 border-b border-slate-700">
        {(['queue', 'map', 'network', 'reports'] as const).map((view) => (
          <button
            key={view}
            onClick={() => setActiveView(view)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeView === view
                ? 'border-amber-500 text-amber-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {view === 'queue' && <FileText size={16} />}
            {view === 'map' && <Map size={16} />}
            {view === 'network' && <Network size={16} />}
            {view === 'reports' && <FileText size={16} />}
            {view === 'queue' && 'Cola de Alertas'}
            {view === 'map' && 'Mapa Táctico'}
            {view === 'network' && 'Grafos de Red'}
            {view === 'reports' && 'Informes'}
          </button>
        ))}
      </div>

      {activeView === 'queue' && (
        <AlertQueue
          alerts={alertsData?.items ?? []}
          isLoading={alertsLoading}
          isError={alertsError}
          filters={filters}
          onFiltersChange={setFilters}
          total={alertsData?.total ?? 0}
          page={filters.page ?? 1}
          pageSize={filters.page_size ?? 20}
          onPageChange={(p) => setFilters((f) => ({ ...f, page: p }))}
        />
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
