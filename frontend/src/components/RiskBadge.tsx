import type { RiskLevel } from '@/lib/types'
import { cn, RISK_BG_CLASSES, RISK_LABELS } from '@/lib/utils'

interface RiskBadgeProps {
  level: RiskLevel
  className?: string
}

export function RiskBadge({ level, className }: RiskBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold font-mono tracking-wide',
        RISK_BG_CLASSES[level],
        className,
      )}
      aria-label={`Nivel de riesgo: ${RISK_LABELS[level]}`}
    >
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: 'currentColor' }}
        aria-hidden="true"
      />
      {level} — {RISK_LABELS[level]}
    </span>
  )
}
