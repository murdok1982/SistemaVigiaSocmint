import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { ReviewAction } from '@/lib/types'
import { AnalystPanel } from '@/components/AnalystPanel'
import { RiskBadge } from '@/components/RiskBadge'
import { formatTimestamp, RISK_COLORS, riskScorePercent } from '@/lib/utils'
import { AlertTriangle, ArrowLeft, Loader2 } from 'lucide-react'

export function AlertDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: alert, isLoading, isError } = useQuery({
    queryKey: ['alert', id],
    queryFn: () => api.getAlert(id!),
    enabled: Boolean(id),
  })

  const { mutateAsync: submitReview, isPending: isSubmitting } = useMutation({
    mutationFn: ({ action, notes, analystId }: { action: ReviewAction; notes: string; analystId: string }) =>
      api.reviewAlert(id!, { action, notes, analyst_id: analystId }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['alerts'] })
      void queryClient.invalidateQueries({ queryKey: ['alert', id] })
      void queryClient.invalidateQueries({ queryKey: ['health'] })
      navigate('/')
    },
  })

  const handleReview = async (action: ReviewAction, notes: string, analystId: string) => {
    await submitReview({ action, notes, analystId })
  }

  if (isLoading) {
    return (
      <main className="flex items-center justify-center min-h-96 text-slate-400" role="status">
        <Loader2 className="animate-spin mr-2" size={20} aria-hidden="true" />
        Cargando alerta...
      </main>
    )
  }

  if (isError || !alert) {
    return (
      <main className="p-6">
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-6 text-center text-red-400" role="alert">
          No se pudo cargar la alerta. Verifica el ID o la conexión con el backend.
        </div>
      </main>
    )
  }

  const scorePercent = riskScorePercent(alert.risk_score)
  const isReviewed = alert.status !== 'PENDIENTE'

  return (
    <main className="p-6 max-w-4xl mx-auto space-y-6">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400 rounded"
      >
        <ArrowLeft size={16} aria-hidden="true" />
        Volver a la cola
      </button>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="font-mono text-xs font-medium text-slate-300 uppercase tracking-widest bg-slate-700 px-2 py-0.5 rounded">
              {alert.platform}
            </span>
            <RiskBadge level={alert.risk_level} />
            {isReviewed && (
              <span className="text-xs bg-slate-700 text-slate-400 px-2 py-0.5 rounded font-mono">
                {alert.status}
              </span>
            )}
          </div>
          <p className="font-mono text-xs text-slate-500">ID: {alert.id}</p>
        </div>
        <time className="text-xs text-slate-500 font-mono" dateTime={alert.created_at}>
          {formatTimestamp(alert.created_at)}
        </time>
      </div>

      <section aria-label="Puntuación de riesgo" className="rounded-lg border border-slate-700 bg-slate-800 p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-slate-400">Risk Score</span>
          <span className="font-mono text-2xl font-bold text-slate-100">{scorePercent}%</span>
        </div>
        <div
          className="h-3 rounded-full bg-slate-700 overflow-hidden"
          role="progressbar"
          aria-valuenow={scorePercent}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="h-full rounded-full transition-all"
            style={{ width: `${scorePercent}%`, backgroundColor: RISK_COLORS[alert.risk_level] }}
          />
        </div>
      </section>

      <section aria-label="Contenido analizado" className="rounded-lg border border-slate-700 bg-slate-800 p-4">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">
          Contenido analizado
        </h2>
        <pre className="font-mono text-sm text-slate-300 leading-relaxed whitespace-pre-wrap break-words">
          {alert.content_full}
        </pre>
      </section>

      {alert.indicators.length > 0 && (
        <section aria-label="Indicadores detectados">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">
            Indicadores detectados ({alert.indicators.length})
          </h2>
          <div className="space-y-2">
            {alert.indicators.map((ind, i) => (
              <article key={i} className="rounded-lg border border-slate-700 bg-slate-800 p-3 flex gap-3">
                <AlertTriangle size={16} className="text-amber-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold text-slate-300 font-mono uppercase tracking-wide">
                      {ind.type}
                    </span>
                    <span className="text-xs bg-slate-700 text-slate-400 px-2 py-0.5 rounded font-mono">
                      {ind.value}
                    </span>
                  </div>
                  <p className="text-sm text-slate-400">{ind.explanation}</p>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {isReviewed ? (
        <section aria-label="Decisión registrada" className="rounded-lg border border-slate-700 bg-slate-800 p-4">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">Decisión registrada</h2>
          <p className="text-sm text-slate-300">Estado: <span className="font-mono text-slate-200">{alert.status}</span></p>
          {alert.reviewed_by && (
            <p className="text-sm text-slate-300">Analista: <span className="font-mono text-slate-200">{alert.reviewed_by}</span></p>
          )}
          {alert.reviewed_at && (
            <p className="text-sm text-slate-300">
              Revisado: <time dateTime={alert.reviewed_at}>{formatTimestamp(alert.reviewed_at)}</time>
            </p>
          )}
          {alert.analyst_notes && (
            <p className="text-sm text-slate-400 mt-2 font-mono border-t border-slate-700 pt-2">{alert.analyst_notes}</p>
          )}
        </section>
      ) : (
        <AnalystPanel
          alertId={alert.id}
          onSubmit={handleReview}
          isSubmitting={isSubmitting}
        />
      )}
    </main>
  )
}
