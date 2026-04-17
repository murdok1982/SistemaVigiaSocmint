import type { AlertFilters, AlertListItem, AlertStatus, RiskLevel } from '@/lib/types'
import { AlertCard } from './AlertCard'
import { Inbox, Loader2 } from 'lucide-react'

const RISK_LEVELS: RiskLevel[] = ['ROJO', 'NARANJA', 'AMARILLO', 'VERDE']
const PLATFORMS = ['Twitter', 'Telegram', 'Facebook', 'Reddit', 'Web']
const STATUSES: { value: AlertStatus; label: string }[] = [
  { value: 'PENDIENTE',      label: 'Pendiente' },
  { value: 'ESCALADA',       label: 'Escalada' },
  { value: 'ARCHIVADA',      label: 'Archivada' },
  { value: 'FALSO_POSITIVO', label: 'Falso positivo' },
]

interface AlertQueueProps {
  alerts: AlertListItem[]
  isLoading: boolean
  isError: boolean
  filters: AlertFilters
  onFiltersChange: (f: AlertFilters) => void
  total: number
  page: number
  pageSize: number
  onPageChange: (p: number) => void
}

export function AlertQueue({
  alerts, isLoading, isError, filters, onFiltersChange,
  total, page, pageSize, onPageChange,
}: AlertQueueProps) {
  const totalPages = Math.ceil(total / pageSize)

  return (
    <section aria-label="Cola de alertas">
      <div className="flex flex-wrap gap-3 mb-4">
        <div>
          <label htmlFor="filter-level" className="sr-only">Filtrar por nivel</label>
          <select
            id="filter-level"
            value={filters.risk_level ?? ''}
            onChange={(e) => onFiltersChange({ ...filters, risk_level: (e.target.value as RiskLevel) || undefined, page: 1 })}
            className="bg-slate-800 border border-slate-600 text-slate-200 text-sm rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
          >
            <option value="">Todos los niveles</option>
            {RISK_LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>

        <div>
          <label htmlFor="filter-platform" className="sr-only">Filtrar por plataforma</label>
          <select
            id="filter-platform"
            value={filters.platform ?? ''}
            onChange={(e) => onFiltersChange({ ...filters, platform: e.target.value || undefined, page: 1 })}
            className="bg-slate-800 border border-slate-600 text-slate-200 text-sm rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
          >
            <option value="">Todas las plataformas</option>
            {PLATFORMS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>

        <div>
          <label htmlFor="filter-status" className="sr-only">Filtrar por estado</label>
          <select
            id="filter-status"
            value={filters.status ?? ''}
            onChange={(e) => onFiltersChange({ ...filters, status: (e.target.value as AlertStatus) || undefined, page: 1 })}
            className="bg-slate-800 border border-slate-600 text-slate-200 text-sm rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
          >
            <option value="">Todos los estados</option>
            {STATUSES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </div>

        <span className="ml-auto text-sm text-slate-400 self-center">
          {total} alerta{total !== 1 ? 's' : ''}
        </span>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-16 text-slate-400" role="status">
          <Loader2 className="animate-spin mr-2" size={20} aria-hidden="true" />
          Cargando alertas...
        </div>
      )}

      {isError && !isLoading && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-6 text-center text-red-400" role="alert">
          Error al cargar alertas. Verifica la conexión con el backend.
        </div>
      )}

      {!isLoading && !isError && alerts.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-slate-500">
          <Inbox size={40} aria-hidden="true" className="mb-3" />
          <p className="text-sm">No hay alertas que coincidan con los filtros.</p>
        </div>
      )}

      {!isLoading && !isError && alerts.length > 0 && (
        <div className="space-y-3">
          {alerts.map((alert) => <AlertCard key={alert.id} alert={alert} />)}
        </div>
      )}

      {totalPages > 1 && (
        <nav className="flex items-center justify-between mt-6 pt-4 border-t border-slate-700" aria-label="Paginación">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="px-4 py-2 text-sm rounded-md border border-slate-600 text-slate-300 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Anterior
          </button>
          <span className="text-sm text-slate-400">Página {page} de {totalPages}</span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="px-4 py-2 text-sm rounded-md border border-slate-600 text-slate-300 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Siguiente
          </button>
        </nav>
      )}
    </section>
  )
}
