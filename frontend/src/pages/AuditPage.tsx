import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { FileText, Filter, Shield } from 'lucide-react'
import type { AuditEntry, AuditFilters } from '@/lib/types'

export function AuditPage() {
  const [filters, setFilters] = useState<AuditFilters>({ page: 1, page_size: 50 })
  const [showFilters, setShowFilters] = useState(false)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['audit-log', filters],
    queryFn: () => api.getAuditLog(filters),
    refetchInterval: 60_000,
  })

  return (
    <main className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Log de Auditoría</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Registro inmutable de todas las acciones del sistema
          </p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-3 py-1.5 text-xs rounded-md bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
        >
          <Filter size={14} />
          Filtros
        </button>
      </div>

      {showFilters && (
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Agente</label>
              <input
                type="text"
                value={filters.agent || ''}
                onChange={(e) => setFilters({ ...filters, agent: e.target.value || undefined })}
                placeholder="Ej: ANALYSIS_AGENT"
                className="w-full px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-sm text-slate-100"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tipo de Acción</label>
              <input
                type="text"
                value={filters.action_type || ''}
                onChange={(e) => setFilters({ ...filters, action_type: e.target.value || undefined })}
                placeholder="Ej: review_escalar"
                className="w-full px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-sm text-slate-100"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Fecha Desde</label>
              <input
                type="date"
                value={filters.date_from || ''}
                onChange={(e) => setFilters({ ...filters, date_from: e.target.value || undefined })}
                className="w-full px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-sm text-slate-100"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Fecha Hasta</label>
              <input
                type="date"
                value={filters.date_to || ''}
                onChange={(e) => setFilters({ ...filters, date_to: e.target.value || undefined })}
                className="w-full px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-sm text-slate-100"
              />
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-8 text-slate-500">Cargando logs...</div>
      ) : isError ? (
        <div className="text-center py-8 text-red-400">Error cargando logs de auditoría</div>
      ) : (
        <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700 bg-slate-900">
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400">Timestamp</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400">Agente</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400">Acción</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400">Alerta ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400">Detalles</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((entry: AuditEntry) => (
                  <tr key={entry.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                    <td className="px-4 py-3 text-xs text-slate-300">
                      {new Date(entry.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-xs bg-slate-700 text-slate-300">
                        {entry.agent}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-300">{entry.action_type}</td>
                    <td className="px-4 py-3 text-xs text-slate-400 font-mono">
                      {entry.alert_id?.slice(0, 8) || '-'}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400 max-w-md truncate">
                      {entry.details}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {data && data.total > 0 && (
            <div className="px-4 py-3 border-t border-slate-700 flex items-center justify-between">
              <span className="text-xs text-slate-400">
                Mostrando {data.items.length} de {data.total} entradas
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setFilters({ ...filters, page: (filters.page || 1) - 1 })}
                  disabled={filters.page <= 1}
                  className="px-3 py-1 text-xs bg-slate-700 text-slate-300 rounded disabled:opacity-50"
                >
                  Anterior
                </button>
                <span className="px-3 py-1 text-xs text-slate-300">
                  Página {filters.page || 1}
                </span>
                <button
                  onClick={() => setFilters({ ...filters, page: (filters.page || 1) + 1 })}
                  disabled={!data.items.length || data.items.length < (filters.page_size || 50)}
                  className="px-3 py-1 text-xs bg-slate-700 text-slate-300 rounded disabled:opacity-50"
                >
                  Siguiente
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </main>
  )
}
