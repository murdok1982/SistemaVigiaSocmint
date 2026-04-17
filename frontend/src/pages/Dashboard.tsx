import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { AlertFilters } from '@/lib/types'
import { AlertQueue } from '@/components/AlertQueue'
import { RunAnalysisModal } from '@/components/RunAnalysisModal'
import { StatsBar } from '@/components/StatsBar'
import { Play } from 'lucide-react'

export function Dashboard() {
  const [filters, setFilters] = useState<AlertFilters>({ page: 1, page_size: 20 })
  const [showAnalysisModal, setShowAnalysisModal] = useState(false)

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
          <h1 className="text-xl font-bold text-slate-100">Centro de Monitoreo</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Sistema OSINT/SOCMINT — Revisión humana obligatoria antes de cualquier acción
          </p>
        </div>
        <button
          onClick={() => setShowAnalysisModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-md bg-amber-600 text-sm font-semibold text-white hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-400"
        >
          <Play size={15} aria-hidden="true" />
          Lanzar análisis
        </button>
      </div>

      <StatsBar stats={stats} isLoading={statsLoading} />

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

      {showAnalysisModal && (
        <RunAnalysisModal onClose={() => setShowAnalysisModal(false)} />
      )}
    </main>
  )
}
