import { Link } from 'react-router-dom'
import type { AlertListItem } from '@/lib/types'
import { AlertTriangle, Shield, Clock, ExternalLink } from 'lucide-react'
import { RISK_CARD_CLASSES, RISK_BADGE_CLASSES, STATUS_TEXT_CLASSES } from '@/lib/utils'

export function AlertCard({ alert }: { alert: AlertListItem }) {
  return (
    <Link to={`/alerts/${alert.id}`} className="block" aria-label={`Alerta ${alert.risk_level} — ${alert.platform} — ${alert.status}`}>
      <div className={`border rounded-lg p-4 transition-all hover:border-amber-500/50 ${RISK_CARD_CLASSES[alert.risk_level]}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${RISK_BADGE_CLASSES[alert.risk_level]}`}>
                {alert.risk_level}
              </span>
              <span className="px-2 py-0.5 rounded text-xs bg-slate-700 text-slate-300">
                {alert.platform}
              </span>
              <span className={`text-xs font-medium ${STATUS_TEXT_CLASSES[alert.status]}`}>
                {alert.status}
              </span>
            </div>
            <p className="text-sm text-slate-200 line-clamp-2 mb-2">
              {alert.content_excerpt}
            </p>
            <div className="flex items-center gap-4 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <Clock size={12} aria-hidden="true" />
                {new Date(alert.created_at).toLocaleString()}
              </span>
              <span className="flex items-center gap-1">
                <AlertTriangle size={12} aria-hidden="true" />
                {(alert.risk_score * 100).toFixed(0)}%
              </span>
              {alert.indicators.length > 0 && (
                <span className="flex items-center gap-1">
                  <Shield size={12} aria-hidden="true" />
                  {alert.indicators.length} indicador(es)
                </span>
              )}
            </div>
          </div>
          <ExternalLink size={16} className="text-slate-500 flex-shrink-0 mt-1" aria-hidden="true" />
        </div>
      </div>
    </Link>
  )
}
