import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Filter, Key, Eye, Send, Archive, XCircle, Play, Users, RefreshCw, ChevronRight } from 'lucide-react'
import type { AuditEntry, AuditFilters } from '@/lib/types'

function getAgentColor(agent: string) {
  const a = agent.toUpperCase()
  if (a.includes('AUTH') || a.includes('LOGIN')) return 'bg-blue-500/20 text-blue-400 border-blue-500/40'
  if (a.includes('ANALYST') || a.includes('ANALYSIS')) return 'bg-amber-500/20 text-amber-400 border-amber-500/40'
  if (a.includes('ORCHESTRATOR') || a.includes('ORCH')) return 'bg-purple-500/20 text-purple-400 border-purple-500/40'
  return 'bg-slate-700 text-slate-300 border-slate-600'
}

function getActionIcon(action: string) {
  const a = action.toLowerCase()
  if (a.includes('login') || a.includes('auth')) return <Key size={14} className="text-blue-400" />
  if (a.includes('review') || a.includes('view') || a.includes('read')) return <Eye size={14} className="text-amber-400" />
  if (a.includes('escalar') || a.includes('escalat')) return <Send size={14} className="text-red-400" />
  if (a.includes('archiv')) return <Archive size={14} className="text-slate-400" />
  if (a.includes('falso') || a.includes('dismiss')) return <XCircle size={14} className="text-green-400" />
  if (a.includes('analysis') || a.includes('run') || a.includes('launch')) return <Play size={14} className="text-purple-400" />
  if (a.includes('orchestrat')) return <Users size={14} className="text-purple-400" />
  if (a.includes('export') || a.includes('stix')) return <RefreshCw size={14} className="text-cyan-400" />
  return <ChevronRight size={14} className="text-slate-400" />
}

export function AuditPage() {
  const [filters, setFilters] = useState<AuditFilters>({ page: 1, page_size: 50 })
  const [showFilters, setShowFilters] = useState(false)
  const [goToPage, setGoToPage] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['audit-log', filters],
    queryFn: () => api.getAuditLog(filters),
    refetchInterval: 60_000,
  })

  const totalPages = data ? Math.ceil(data.total / (filters.page_size || 50)) : 0

  const handleGoToPage = () => {
    const p = parseInt(goToPage, 10)
    if (!isNaN(p) && p >= 1 && p <= totalPages) {
      setFilters({ ...filters, page: p })
      setGoToPage('')
    }
  }

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
          aria-expanded={showFilters}
          aria-controls="audit-filters-panel"
        >
          <Filter size={14} aria-hidden="true" />
          Filtros
        </button>
      </div>

      {showFilters && (
        <div id="audit-filters-panel" className="bg-slate-800 p-4 rounded-lg border border-slate-700 space-y-3" role="region" aria-label="Filtros de auditoría">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <label htmlFor="filter-agent" className="block text-xs text-slate-400 mb-1">Agente</label>
              <input
                id="filter-agent"
                type="text"
                value={filters.agent || ''}
                onChange={(e) => setFilters({ ...filters, agent: e.target.value || undefined })}
                placeholder="Ej: ANALYSIS_AGENT"
                className="w-full px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-sm text-slate-100 placeholder:text-slate-500"
              />
            </div>
            <div>
              <label htmlFor="filter-action" className="block text-xs text-slate-400 mb-1">Tipo de Acción</label>
              <input
                id="filter-action"
                type="text"
                value={filters.action_type || ''}
                onChange={(e) => setFilters({ ...filters, action_type: e.target.value || undefined })}
                placeholder="Ej: review_escalar"
                className="w-full px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-sm text-slate-100 placeholder:text-slate-500"
              />
            </div>
            <div>
              <label htmlFor="filter-date-from" className="block text-xs text-slate-400 mb-1">Fecha Desde</label>
              <input
                id="filter-date-from"
                type="date"
                value={filters.date_from || ''}
                onChange={(e) => setFilters({ ...filters, date_from: e.target.value || undefined })}
                className="w-full px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-sm text-slate-100"
              />
            </div>
            <div>
              <label htmlFor="filter-date-to" className="block text-xs text-slate-400 mb-1">Fecha Hasta</label>
              <input
                id="filter-date-to"
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
        <div className="text-center py-8 text-slate-400" role="status">
          <span className="sr-only">Cargando</span>
          Cargando logs...
        </div>
      ) : isError ? (
        <div className="text-center py-8 text-red-400" role="alert">Error cargando logs de auditoría</div>
      ) : (
        <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm" aria-label="Entradas del log de auditoría">
              <thead>
                <tr className="border-b border-slate-700 bg-slate-900">
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-slate-400">Timestamp</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-slate-400">Agente</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-slate-400">Acción</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-slate-400">Alerta ID</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-slate-400">Detalles</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((entry: AuditEntry) => (
                  <tr key={entry.id} className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3 text-xs text-slate-300">
                      <time dateTime={entry.timestamp}>{new Date(entry.timestamp).toLocaleString()}</time>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-0.5 rounded text-xs border ${getAgentColor(entry.agent)}`}>
                        {entry.agent}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="flex items-center gap-1.5 text-xs text-slate-300">
                        {getActionIcon(entry.action_type)}
                        {entry.action_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400 font-mono">
                      {entry.alert_id?.slice(0, 8) || '—'}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400 max-w-md truncate" title={entry.details}>
                      {entry.details}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {data && data.total > 0 && (
            <nav className="px-4 py-3 border-t border-slate-700 flex flex-col sm:flex-row items-center justify-between gap-3" aria-label="Paginación de auditoría">
              <span className="text-xs text-slate-400">
                Mostrando {data.items.length} de {data.total} entradas
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setFilters({ ...filters, page: (filters.page || 1) - 1 })}
                  disabled={(filters.page ?? 1) <= 1}
                  className="px-3 py-1 text-xs bg-slate-700 text-slate-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-600 transition-colors"
                  aria-label="Página anterior"
                >
                  Anterior
                </button>
                <span className="px-3 py-1 text-xs text-slate-300" aria-current="page">
                  Página {filters.page || 1} de {totalPages}
                </span>
                <button
                  onClick={() => setFilters({ ...filters, page: (filters.page || 1) + 1 })}
                  disabled={!data.items.length || data.items.length < (filters.page_size || 50)}
                  className="px-3 py-1 text-xs bg-slate-700 text-slate-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-600 transition-colors"
                  aria-label="Página siguiente"
                >
                  Siguiente
                </button>
                <div className="flex items-center gap-1 ml-2 pl-2 border-l border-slate-700">
                  <label htmlFor="go-to-page" className="text-xs text-slate-500">Ir a:</label>
                  <input
                    id="go-to-page"
                    type="number"
                    min={1}
                    max={totalPages}
                    value={goToPage}
                    onChange={(e) => setGoToPage(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleGoToPage()}
                    className="w-14 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-amber-500"
                    placeholder="#"
                  />
                  <button
                    onClick={handleGoToPage}
                    disabled={!goToPage}
                    className="px-2 py-1 text-xs bg-amber-600 text-white rounded disabled:opacity-50 hover:bg-amber-500 transition-colors"
                  >
                    Ir
                  </button>
                </div>
              </div>
            </nav>
          )}
        </div>
      )}
    </main>
  )
}
