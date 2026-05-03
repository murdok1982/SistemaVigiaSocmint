import { useState } from 'react'
import type { AlertListItem, AlertFilters } from '@/lib/types'
import { AlertCard } from './AlertCard'
import { ChevronLeft, ChevronRight, Filter, Shield } from 'lucide-react'

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
}

export function AlertQueue({ alerts, isLoading, isError, filters, onFiltersChange, total, page, onPageChange }: Props) {
  const [showFilters, setShowFilters] = useState(false)
  const totalPages = Math.ceil(total / (filters.page_size || 20))

  return (
    <div className="space-y-4">
      {/* Toolbar */}
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
        <div className="text-xs text-slate-400">
          {total} alertas totales
        </div>
      </div>

      {/* Filtros expandibles */}
      {showFilters && (
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nivel de Riesgo</label>
              <select
                value={filters.risk_level || ''}
                onChange={(e) => onFiltersChange({ ...filters, risk_level: e.target.value as any || undefined })}
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
                onChange={(e) => onFiltersChange({ ...filters, status: e.target.value as any || undefined })}
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

      {/* Lista de alertas */}
      {isLoading ? (
        <div className="text-center py-8 text-slate-500">Cargando alertas...</div>
      ) : isError ? (
        <div className="text-center py-8 text-red-400">Error cargando alertas</div>
      ) : alerts.length === 0 ? (
        <div className="text-center py-8 text-slate-500">
          <Shield size={48} className="mx-auto mb-2 text-slate-600" />
          No hay alertas que coincidan con los filtros
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
        </div>
      )}

      {/* Paginación */}
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
