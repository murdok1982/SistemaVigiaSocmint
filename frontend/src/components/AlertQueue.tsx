import { useState } from 'react'
import type { AlertListItem, AlertFilters, RiskLevel, AlertStatus } from '@/lib/types'
import { AlertCard } from './AlertCard'
import { ChevronLeft, ChevronRight, Filter, Shield, AlertOctagon, RefreshCw, Play, Download } from 'lucide-react'

interface Props {
  alerts: AlertListItem[]
  isLoading: boolean
  isError: boolean
  filters: AlertFilters
  onFiltersChange: (f: AlertFilters) => void
  total: number
  page: number
  pageSize: number
  onPageChange: (page: number) => void
  onRetry?: () => void
  onLaunchAnalysis?: () => void
}

function SkeletonCard() {
  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 p-4 animate-pulse">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-slate-700 rounded-full" />
          <div className="space-y-1.5">
            <div className="h-3 w-20 bg-slate-700 rounded" />
            <div className="h-2.5 w-32 bg-slate-700 rounded" />
          </div>
        </div>
        <div className="h-5 w-16 bg-slate-700 rounded-full" />
      </div>
      <div className="space-y-2">
        <div className="h-2.5 bg-slate-700 rounded w-full" />
        <div className="h-2.5 bg-slate-700 rounded w-4/5" />
      </div>
      <div className="flex gap-2 mt-3">
        <div className="h-5 w-14 bg-slate-700 rounded" />
        <div className="h-5 w-14 bg-slate-700 rounded" />
        <div className="h-5 w-14 bg-slate-700 rounded" />
      </div>
    </div>
  )
}

export function AlertQueue({ alerts, isLoading, isError, filters, onFiltersChange, total, page, onPageChange, onRetry, onLaunchAnalysis }: Props) {
  const [showFilters, setShowFilters] = useState(false)
  const totalPages = Math.ceil(total / (filters.page_size || 20))

  const exportCSV = () => {
    const headers = ['id', 'platform', 'risk_level', 'status', 'risk_score', 'content_excerpt', 'created_at']
    const rows = alerts.map((a) =>
      [a.id, a.platform, a.risk_level, a.status, a.risk_score, `"${a.content_excerpt.replace(/"/g, '""')}"`, a.created_at].join(',')
    )
    const csv = [headers.join(','), ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `alertas_${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  const exportJSON = () => {
    const json = JSON.stringify(alerts, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `alertas_${new Date().toISOString().slice(0, 10)}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-md bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
          >
            <Filter size={14} />
            Filtros
          </button>
          {filters.risk_level && (
            <span className="px-2 py-1 text-xs rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/50">
              {filters.risk_level}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={exportCSV}
            disabled={alerts.length === 0}
            className="flex items-center gap-1 px-2.5 py-1.5 text-xs rounded-md bg-slate-700 text-slate-300 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Download size={13} />
            CSV
          </button>
          <button
            onClick={exportJSON}
            disabled={alerts.length === 0}
            className="flex items-center gap-1 px-2.5 py-1.5 text-xs rounded-md bg-slate-700 text-slate-300 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Download size={13} />
            JSON
          </button>
          <span className="text-xs text-slate-400">
            {total} alertas totales
          </span>
        </div>
      </div>

      {showFilters && (
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nivel de Riesgo</label>
              <select
                value={filters.risk_level || ''}
                onChange={(e) => onFiltersChange({ ...filters, risk_level: (e.target.value || undefined) as RiskLevel | undefined })}
                className="w-full px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-sm text-slate-100"
              >
                <option value="">Todos</option>
                <option value="ROJO">ROJO</option>
                <option value="NARANJA">NARANJA</option>
                <option value="AMARILLO">AMARILLO</option>
                <option value="VERDE">VERDE</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Plataforma</label>
              <select
                value={filters.platform || ''}
                onChange={(e) => onFiltersChange({ ...filters, platform: e.target.value || undefined })}
                className="w-full px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-sm text-slate-100"
              >
                <option value="">Todas</option>
                <option value="twitter">Twitter</option>
                <option value="telegram">Telegram</option>
                <option value="reddit">Reddit</option>
                <option value="facebook">Facebook</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Estado</label>
              <select
                value={filters.status || ''}
                onChange={(e) => onFiltersChange({ ...filters, status: (e.target.value || undefined) as AlertStatus | undefined })}
                className="w-full px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-sm text-slate-100"
              >
                <option value="">Todos</option>
                <option value="PENDIENTE">PENDIENTE</option>
                <option value="ESCALADA">ESCALADA</option>
                <option value="ARCHIVADA">ARCHIVADA</option>
                <option value="FALSO_POSITIVO">FALSO POSITIVO</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end">
            <button
              onClick={() => onFiltersChange({ page: 1, page_size: 20 })}
              className="px-3 py-1 text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              Limpiar filtros
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-3" role="status" aria-label="Cargando alertas">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonCard key={i} />
          ))}
          <span className="sr-only">Cargando alertas</span>
        </div>
      ) : isError ? (
        <div className="text-center py-12" role="alert">
          <AlertOctagon size={48} className="mx-auto mb-3 text-red-400/60" />
          <p className="text-red-400 font-medium mb-1">Error al cargar las alertas</p>
          <p className="text-slate-500 text-sm mb-4">No se pudo conectar con el servidor. Verifica tu conexión e inténtalo de nuevo.</p>
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-red-600/20 border border-red-500/40 text-red-300 text-sm font-medium hover:bg-red-600/30 transition-colors"
          >
            <RefreshCw size={14} />
            Reintentar
          </button>
        </div>
      ) : alerts.length === 0 ? (
        <div className="text-center py-16">
          <Shield size={64} className="mx-auto mb-4 text-slate-600/50" aria-hidden="true" />
          <p className="text-slate-300 font-medium text-lg mb-1">Sin alertas en cola</p>
          <p className="text-slate-500 text-sm mb-6 max-w-sm mx-auto">
            No se han detectado alertas que coincidan con los filtros actuales. Lanza un nuevo análisis para comenzar el monitoreo.
          </p>
          <button
            onClick={onLaunchAnalysis}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-amber-600 text-sm font-semibold text-white hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-400"
          >
            <Play size={15} />
            Lanzar Análisis
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="p-1.5 rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-sm text-slate-300">
            Página {page} de {totalPages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="p-1.5 rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  )
}
