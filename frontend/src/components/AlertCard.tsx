import { useNavigate } from 'react-router-dom'
import type { AlertListItem } from '@/lib/types'
import { RiskBadge } from './RiskBadge'
import { cn, formatTimestamp, riskScorePercent, RISK_COLORS } from '@/lib/utils'
import { AlertTriangle, ChevronRight, Clock } from 'lucide-react'

interface AlertCardProps {
  alert: AlertListItem
}

export function AlertCard({ alert }: AlertCardProps) {
  const navigate = useNavigate()
  const scorePercent = riskScorePercent(alert.risk_score)

  return (
    <article
      className={cn(
        'group relative rounded-lg border border-slate-700 bg-slate-800 p-4',
        'transition-colors hover:border-slate-500 hover:bg-slate-700/50 cursor-pointer',
        'focus-within:ring-2 focus-within:ring-slate-400',
      )}
      onClick={() => navigate(`/alerts/${alert.id}`)}
    >
      <button
        className="absolute inset-0 rounded-lg"
        onClick={() => navigate(`/alerts/${alert.id}`)}
        aria-label={`Ver detalle de alerta de ${alert.platform} — nivel ${alert.risk_level}`}
      />

      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-mono text-xs font-medium text-slate-300 uppercase tracking-widest bg-slate-700 px-2 py-0.5 rounded">
            {alert.platform}
          </span>
          <RiskBadge level={alert.risk_level} />
        </div>
        <ChevronRight
          size={16}
          className="text-slate-500 group-hover:text-slate-300 transition-colors flex-shrink-0 mt-0.5"
          aria-hidden="true"
        />
      </div>

      <p className="font-mono text-sm text-slate-300 leading-relaxed mb-3 line-clamp-2">
        {alert.content_excerpt}
      </p>

      {alert.indicators.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {alert.indicators.slice(0, 4).map((ind, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded font-mono"
            >
              <AlertTriangle size={10} aria-hidden="true" />
              {ind.type}
            </span>
          ))}
          {alert.indicators.length > 4 && (
            <span className="text-xs text-slate-500 px-2 py-0.5">
              +{alert.indicators.length - 4} más
            </span>
          )}
        </div>
      )}

      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div
            className="h-1.5 flex-1 rounded-full bg-slate-700 overflow-hidden"
            role="progressbar"
            aria-valuenow={scorePercent}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Risk score: ${scorePercent}%`}
          >
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${scorePercent}%`, backgroundColor: RISK_COLORS[alert.risk_level] }}
            />
          </div>
          <span className="font-mono text-xs text-slate-400 flex-shrink-0">{scorePercent}%</span>
        </div>

        <div className="flex items-center gap-1 text-xs text-slate-500 flex-shrink-0">
          <Clock size={12} aria-hidden="true" />
          <time dateTime={alert.created_at}>{formatTimestamp(alert.created_at)}</time>
        </div>
      </div>
    </article>
  )
}
