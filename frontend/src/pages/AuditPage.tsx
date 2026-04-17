import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { AuditEntry, AuditFilters } from '@/lib/types'
import { AuditLog } from '@/components/AuditLog'

export function AuditPage() {
  const [filters, setFilters] = useState<AuditFilters>({ page: 1, page_size: 50 })

  const { data, isLoading, isError } = useQuery({
    queryKey: ['audit-log', filters],
    queryFn: () => api.getAuditLog(filters),
  })

  const handleExportCsv = () => {
    if (!data?.items.length) return

    const headers = ['id', 'timestamp', 'agent', 'action_type', 'alert_id', 'details']
    const rows = data.items.map((e: AuditEntry) =>
      [
        e.id,
        e.timestamp,
        e.agent,
        e.action_type,
        e.alert_id ?? '',
        `"${e.details.replace(/"/g, '""')}"`,
      ].join(',')
    )

    const csv = [headers.join(','), ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `audit-log-${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <main className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100">Log de Auditoría</h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Registro completo de acciones del sistema y decisiones de analistas
        </p>
      </div>

      <AuditLog
        entries={data?.items ?? []}
        isLoading={isLoading}
        isError={isError}
        filters={filters}
        onFiltersChange={setFilters}
        total={data?.total ?? 0}
        page={filters.page ?? 1}
        pageSize={filters.page_size ?? 50}
        onPageChange={(p) => setFilters((f) => ({ ...f, page: p }))}
        onExportCsv={handleExportCsv}
      />
    </main>
  )
}
