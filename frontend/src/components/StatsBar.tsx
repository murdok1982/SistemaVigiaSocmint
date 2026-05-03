import type { SystemStats } from '@/lib/types'
import { Shield, AlertTriangle, CheckCircle, Clock } from 'lucide-react'

interface Props {
  stats: SystemStats | undefined
  isLoading: boolean
}

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

  const statsItems = [
    {
      label: 'Alertas Hoy',
      value: stats.alerts_today,
      icon: <Shield size={20} className="text-amber-400" />,
      color: 'text-amber-400',
    },
    {
      label: 'Pendientes',
      value: stats.pending_review,
      icon: <AlertTriangle size={20} className="text-red-400" />,
      color: 'text-red-400',
    },
    {
      label: 'ROJO',
      value: stats.by_level?.ROJO || 0,
      icon: <AlertTriangle size={20} className="text-red-500" />,
      color: 'text-red-500',
    },
    {
      label: 'NARANJA',
      value: stats.by_level?.NARANJA || 0,
      icon: <Clock size={20} className="text-orange-500" />,
      color: 'text-orange-500',
    },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {statsItems.map((item) => (
        <div key={item.label} className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <div className="flex items-center gap-2 mb-2">
            {item.icon}
            <span className="text-xs text-slate-400">{item.label}</span>
          </div>
          <p className={`text-2xl font-bold ${item.color}`}>{item.value}</p>
        </div>
      ))}
    </div>
  )
}
