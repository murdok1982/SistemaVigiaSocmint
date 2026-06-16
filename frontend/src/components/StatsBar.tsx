import type { RiskLevel, SystemStats } from '@/lib/types'
import { Shield, AlertTriangle, CheckCircle, Clock } from 'lucide-react'
import { RISK_BADGE_CLASSES } from '@/lib/utils'

interface Props {
  stats: SystemStats | undefined
  isLoading: boolean
}

const TOOLTIPS: Record<string, string> = {
  'Alertas Hoy': 'Total de alertas generadas en las últimas 24h',
  'Pendientes': 'Alertas que requieren revisión humana',
  'ROJO': 'Alertas de nivel crítico — acción inmediata requerida',
  'NARANJA': 'Alertas de nivel alto — revisión prioritaria',
  'AMARILLO': 'Alertas de nivel medio — revisión en cola',
  'VERDE': 'Alertas de nivel bajo — informativas',
}

const LEVEL_CONFIG: { key: RiskLevel; icon: React.ReactNode; iconColor: string }[] = [
  { key: 'ROJO', icon: <AlertTriangle size={20} />, iconColor: 'text-red-500' },
  { key: 'NARANJA', icon: <Clock size={20} />, iconColor: 'text-orange-500' },
  { key: 'AMARILLO', icon: <AlertTriangle size={20} />, iconColor: 'text-yellow-500' },
  { key: 'VERDE', icon: <CheckCircle size={20} />, iconColor: 'text-green-500' },
]

export function StatsBar({ stats, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-slate-800 p-4 rounded-lg border border-slate-700 animate-pulse">
            <div className="h-4 bg-slate-700 rounded w-20 mb-2" />
            <div className="h-8 bg-slate-700 rounded w-16" />
          </div>
        ))}
      </div>
    )
  }

  if (!stats) return null

  const levelItems = LEVEL_CONFIG.map(({ key, icon, iconColor }) => ({
    label: key,
    value: stats.by_level?.[key] ?? 0,
    icon,
    iconColor,
    badgeText: RISK_BADGE_CLASSES[key].split(' ').find(c => c.startsWith('text-')) ?? 'text-slate-400',
  }))

  const statsItems = [
    {
      label: 'Alertas Hoy',
      value: stats.alerts_today,
      icon: <Shield size={20} />,
      iconColor: 'text-amber-400',
      badgeText: 'text-amber-400',
    },
    {
      label: 'Pendientes',
      value: stats.pending_review,
      icon: <AlertTriangle size={20} />,
      iconColor: 'text-red-400',
      badgeText: 'text-red-400',
    },
    ...levelItems,
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4" role="region" aria-label="Estadísticas del sistema">
      {statsItems.map((item) => (
        <div
          key={item.label}
          className="bg-slate-800 p-4 rounded-lg border border-slate-700"
          title={TOOLTIPS[item.label] || ''}
        >
          <div className="flex items-center gap-2 mb-2">
            <span className={item.iconColor} aria-hidden="true">{item.icon}</span>
            <span className="text-xs text-slate-400">{item.label}</span>
          </div>
          <p className={`text-2xl font-bold ${item.badgeText}`}>{item.value}</p>
        </div>
      ))}
    </div>
  )
}
