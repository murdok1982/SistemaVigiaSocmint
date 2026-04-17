import type { SystemStats } from '@/lib/types'
import { RISK_COLORS } from '@/lib/utils'
import { Activity, AlertTriangle, Clock, Loader2 } from 'lucide-react'

interface StatsBarProps {
  stats: SystemStats | undefined
  isLoading: boolean
}

export function StatsBar({ stats, isLoading }: StatsBarProps) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-slate-400 text-sm" role="status">
        <Loader2 size={16} className="animate-spin" aria-hidden="true" />
        Cargando estadísticas...
      </div>
    )
  }

  if (!stats) return null

  const statusColor =
    stats.system_status === 'online'
      ? 'text-green-400'
      : stats.system_status === 'degraded'
      ? 'text-yellow-400'
      : 'text-red-400'

  const statusLabel =
    stats.system_status === 'online' ? 'En línea' :
    stats.system_status === 'degraded' ? 'Degradado' : 'Sin conexión'

  return (
    <div
      className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3"
      role="region"
      aria-label="Estadísticas del sistema"
    >
      <div className="rounded-lg border border-slate-700 bg-slate-800 p-3 flex items-center gap-2">
        <Activity size={16} className={statusColor} aria-hidden="true" />
        <div>
          <p className="text-xs text-slate-500">Sistema</p>
          <p className={`text-sm font-semibold ${statusColor}`}>{statusLabel}</p>
        </div>
      </div>

      <div className="rounded-lg border border-slate-700 bg-slate-800 p-3 flex items-center gap-2">
        <AlertTriangle size={16} className="text-slate-400" aria-hidden="true" />
        <div>
          <p className="text-xs text-slate-500">Hoy</p>
          <p className="text-sm font-semibold text-slate-200">{stats.alerts_today}</p>
        </div>
      </div>

      <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/5 p-3 flex items-center gap-2">
        <Clock size={16} className="text-yellow-400" aria-hidden="true" />
        <div>
          <p className="text-xs text-slate-500">Pendientes</p>
          <p className="text-sm font-semibold text-yellow-400">{stats.pending_review}</p>
        </div>
      </div>

      {(['ROJO', 'NARANJA', 'AMARILLO', 'VERDE'] as const).map((level) => (
        <div key={level} className="rounded-lg border border-slate-700 bg-slate-800 p-3 flex items-center gap-2">
          <span
            className="h-3 w-3 rounded-full flex-shrink-0"
            style={{ backgroundColor: RISK_COLORS[level] }}
            aria-hidden="true"
          />
          <div>
            <p className="text-xs text-slate-500">{level.charAt(0) + level.slice(1).toLowerCase()}</p>
            <p className="text-sm font-semibold text-slate-200">{stats.by_level[level] ?? 0}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
