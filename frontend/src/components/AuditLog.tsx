import type { AuditEntry, AuditFilters } from '@/lib/types'
import { formatTimestamp } from '@/lib/utils'
import { Download, Loader2 } from 'lucide-react'

interface AuditLogProps {
  entries: AuditEntry[]
  isLoading: boolean
  isError: boolean
  filters: AuditFilters
  onFiltersChange: (f: AuditFilters) => void
  total: number
  page: number
  pageSize: number
  onPageChange: (p: number) => void
  onExportCsv: () => void
}

export function AuditLog({
  entries, isLoading, isError, filters, onFiltersChange,
  total, page, pageSize, onPageChange, onExportCsv,
}: AuditLogProps) {
  const totalPages = Math.ceil(total / pageSize)

  return (
    <section aria-label="Log de auditoría">
      <div className="flex flex-wrap gap-3 mb-4 items-end">
        <div>
          <label htmlFor="audit-from" className="block text-xs text-slate-400 mb-1">Desde</label>
          <input id="audit-from" type="date" value={filters.date_from ?? ''}
            onChange={(e) => onFiltersChange({ ...filters, date_from: e.target.value || undefined, page: 1 })}
            className="bg-slate-800 border border-slate-600 text-slate-200 text-sm rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
        </div>
        <div>
          <label htmlFor="audit-to" className="block text-xs text-slate-400 mb-1">Hasta</label>
          <input id="audit-to" type="date" value={filters.date_to ?? ''}
            onChange={(e) => onFiltersChange({ ...filters, date_to: e.target.value || undefined, page: 1 })}
            className="bg-slate-800 border border-slate-600 text-slate-200 text-sm rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
        </div>
        <div>
          <label htmlFor="audit-agent" className="block text-xs text-slate-400 mb-1">Agente</label>
          <input id="audit-agent" type="text" value={filters.agent ?? ''} placeholder="Nombre del agente"
            onChange={(e) => onFiltersChange({ ...filters, agent: e.target.value || undefined, page: 1 })}
            className="bg-slate-800 border border-slate-600 text-slate-200 text-sm rounded-md px-3 py-2 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
        </div>
        <div>
          <label htmlFor="audit-type" className="block text-xs text-slate-400 mb-1">Tipo</label>
          <input id="audit-type" type="text" value={filters.action_type ?? ''} placeholder="Tipo de acción"
            onChange={(e) => onFiltersChange({ ...filters, action_type: e.target.value || undefined, page: 1 })}
            className="bg-slate-800 border border-slate-600 text-slate-200 text-sm rounded-md px-3 py-2 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
        </div>
        <button
          onClick={onExportCsv}
          className="ml-auto flex items-center gap-2 rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400"
          aria-label="Exportar CSV"
        >
          <Download size={14} aria-hidden="true" />
          Exportar CSV
        </button>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-12 text-slate-400" role="status">
          <Loader2 className="animate-spin mr-2" size={20} aria-hidden="true" />
          Cargando registros...
        </div>
      )}

      {isError && !isLoading && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-6 text-center text-red-400" role="alert">
          Error al cargar el log de auditoría.
        </div>
      )}

      {!isLoading && !isError && (
        <div className="overflow-x-auto rounded-lg border border-slate-700">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-800/50">
                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">Timestamp</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">Agente</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">Tipo</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">Alerta</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">Detalles</th>
              </tr>
            </thead>
            <tbody>
              {entries.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                    No hay registros con los filtros seleccionados.
                  </td>
                </tr>
              ) : entries.map((entry) => (
                <tr key={entry.id} className="border-b border-slate-700/50 hover:bg-slate-800/40 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-slate-400 whitespace-nowrap">
                    <time dateTime={entry.timestamp}>{formatTimestamp(entry.timestamp)}</time>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-300">{entry.agent}</td>
                  <td className="px-4 py-3">
                    <span className="inline-block text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded font-mono">
                      {entry.action_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-400">{entry.alert_id ?? '—'}</td>
                  <td className="px-4 py-3 text-xs text-slate-400 max-w-xs truncate" title={entry.details}>
                    {entry.details}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <nav className="flex items-center justify-between mt-4 pt-4 border-t border-slate-700" aria-label="Paginación del log">
          <button onClick={() => onPageChange(page - 1)} disabled={page <= 1}
            className="px-4 py-2 text-sm rounded-md border border-slate-600 text-slate-300 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >Anterior</button>
          <span className="text-sm text-slate-400">{total} registros — Página {page} de {totalPages}</span>
          <button onClick={() => onPageChange(page + 1)} disabled={page >= totalPages}
            className="px-4 py-2 text-sm rounded-md border border-slate-600 text-slate-300 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >Siguiente</button>
        </nav>
      )}
    </section>
  )
}
