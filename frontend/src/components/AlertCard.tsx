import { Link } from 'react-router-dom'
import type { AlertListItem } from '@/lib/types'
import { AlertTriangle, Shield, Clock, ExternalLink } from 'lucide-react'

function getRiskColor(level: string): string {
  switch (level) {
    case 'ROJO': return 'border-red-500 bg-red-500/10'
    case 'NARANJA': return 'border-orange-500 bg-orange-500/10'
    case 'AMARILLO': return 'border-yellow-500 bg-yellow-500/10'
    default: return 'border-green-500 bg-green-500/10'
  }
}

function getRiskBadgeColor(level: string): string {
  switch (level) {
    case 'ROJO': return 'bg-red-500/20 text-red-400'
    case 'NARANJA': return 'bg-orange-500/20 text-orange-400'
    case 'AMARILLO': return 'bg-yellow-500/20 text-yellow-400'
    default: return 'bg-green-500/20 text-green-400'
  }
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'PENDIENTE': return 'text-yellow-400'
    case 'ESCALADA': return 'text-red-400'
    case 'ARCHIVADA': return 'text-slate-400'
    case 'FALSO_POSITIVO': return 'text-green-400'
    default: return 'text-slate-400'
  }
}

export function AlertCard({ alert }: { alert: AlertListItem }) {
  return (
    <Link to={`/alerts/${alert.id}`} className="block">
      <div className={`border rounded-lg p-4 transition-all hover:border-amber-500/50 ${getRiskColor(alert.risk_level)}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${getRiskBadgeColor(alert.risk_level)}`}>
                {alert.risk_level}
              </span>
              <span className="px-2 py-0.5 rounded text-xs bg-slate-700 text-slate-300">
                {alert.platform}
              </span>
              <span className={`text-xs font-medium ${getStatusColor(alert.status)}`}>
                {alert.status}
              </span>
            </div>
            <p className="text-sm text-slate-200 line-clamp-2 mb-2">
              {alert.content_excerpt}
            </p>
            <div className="flex items-center gap-4 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <Clock size={12} />
                {new Date(alert.created_at).toLocaleString()}
              </span>
              <span className="flex items-center gap-1">
                <AlertTriangle size={12} />
                {(alert.risk_score * 100).toFixed(0)}%
              </span>
              {alert.indicators.length > 0 && (
                <span className="flex items-center gap-1">
                  <Shield size={12} />
                  {alert.indicators.length} indicador(es)
                </span>
              )}
            </div>
          </div>
          <ExternalLink size={16} className="text-slate-500 flex-shrink-0 mt-1" />
        </div>
      </div>
    </Link>
  )
}
