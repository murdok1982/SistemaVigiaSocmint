import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { ArrowLeft, Shield, AlertTriangle, CheckCircle, XCircle, Archive, Send } from 'lucide-react'
import type { Alert, ReviewRequest } from '@/lib/types'
import { useState } from 'react'

export function AlertDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [notes, setNotes] = useState('')
  const [action, setAction] = useState<'ESCALAR' | 'ARCHIVAR' | 'FALSO_POSITIVO' | null>(null)

  const { data: alert, isLoading, isError } = useQuery({
    queryKey: ['alert', id],
    queryFn: () => api.getAlert(id!),
    enabled: !!id,
  })

  const reviewMutation = useMutation({
    mutationFn: (data: ReviewRequest) => api.reviewAlert(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      navigate('/')
    },
  })

  const handleReview = () => {
    if (!action || !notes) return
    reviewMutation.mutate({
      action,
      notes,
      analyst_id: 'current_user', // En producción: obtener del contexto de auth
    })
  }

  if (isLoading) return <div className="p-6 text-slate-400">Cargando detalles...</div>
  if (isError || !alert) return <div className="p-6 text-red-400">Error cargando la alerta</div>

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'ROJO': return 'text-red-400 bg-red-500/20 border-red-500'
      case 'NARANJA': return 'text-orange-400 bg-orange-500/20 border-orange-500'
      case 'AMARILLO': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500'
      default: return 'text-green-400 bg-green-500/20 border-green-500'
    }
  }

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors"
      >
        <ArrowLeft size={16} />
        Volver a la cola
      </button>

      <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
        {/* Header */}
        <div className={`p-6 border-b border-slate-700 ${getRiskColor(alert.risk_level)} border-l-4`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Shield size={24} className={getRiskColor(alert.risk_level).split(' ')[0]} />
              <div>
                <h1 className="text-2xl font-bold text-slate-100">{alert.risk_level}</h1>
                <p className="text-sm text-slate-400">{alert.platform} • {(alert.risk_score * 100).toFixed(1)}% de riesgo</p>
              </div>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(alert.risk_level)}`}>
              {alert.status}
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          <div>
            <h2 className="text-sm font-semibold text-slate-300 mb-2">Contenido Completo</h2>
            <div className="bg-slate-900 p-4 rounded-lg border border-slate-700">
              <p className="text-slate-200 leading-relaxed">{alert.content_full}</p>
            </div>
          </div>

          {/* Indicators */}
          {alert.indicators.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
                <AlertTriangle size={16} />
                Indicadores Detectados ({alert.indicators.length})
              </h2>
              <div className="space-y-2">
                {alert.indicators.map((ind, idx) => (
                  <div key={idx} className="bg-slate-900 p-3 rounded-lg border border-slate-700">
                    <div className="flex items-start justify-between mb-1">
                      <span className="text-xs font-medium text-amber-400">{ind.type}</span>
                      <span className="text-xs text-slate-500">Confianza: {(ind.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-sm text-slate-300">{ind.value}</p>
                    <p className="text-xs text-slate-400 mt-1">{ind.explanation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-slate-400">Creado:</span>
              <p className="text-slate-200">{new Date(alert.created_at).toLocaleString()}</p>
            </div>
            {alert.reviewed_at && (
              <div>
                <span className="text-slate-400">Revisado:</span>
                <p className="text-slate-200">{new Date(alert.reviewed_at).toLocaleString()}</p>
              </div>
            )}
            {alert.reviewed_by && (
              <div>
                <span className="text-slate-400">Revisado por:</span>
                <p className="text-slate-200">{alert.reviewed_by}</p>
              </div>
            )}
          </div>

          {/* Analyst Notes */}
          {alert.analyst_notes && (
            <div>
              <h2 className="text-sm font-semibold text-slate-300 mb-2">Notas del Analista</h2>
              <div className="bg-slate-900 p-4 rounded-lg border border-slate-700">
                <p className="text-slate-300">{alert.analyst_notes}</p>
              </div>
            </div>
          )}
        </div>

        {/* Actions (if pending) */}
        {alert.status === 'PENDIENTE' && (
          <div className="p-6 border-t border-slate-700 bg-slate-900/50">
            <h2 className="text-sm font-semibold text-slate-300 mb-4">Acción del Analista</h2>
            <div className="space-y-4">
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Justificación de la decisión (mínimo 10 caracteres)..."
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 text-sm placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500"
                rows={4}
              />
              <div className="flex gap-3">
                <button
                  onClick={() => { setAction('ESCALAR'); handleReview() }}
                  disabled={!notes || notes.length < 10 || reviewMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 rounded-md bg-red-600 text-white text-sm font-medium hover:bg-red-500 disabled:opacity-50 transition-colors"
                >
                  <Send size={16} />
                  Escalar
                </button>
                <button
                  onClick={() => { setAction('ARCHIVAR'); handleReview() }}
                  disabled={!notes || notes.length < 10 || reviewMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 rounded-md bg-slate-600 text-white text-sm font-medium hover:bg-slate-500 disabled:opacity-50 transition-colors"
                >
                  <Archive size={16} />
                  Archivar
                </button>
                <button
                  onClick={() => { setAction('FALSO_POSITIVO'); handleReview() }}
                  disabled={!notes || notes.length < 10 || reviewMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 rounded-md bg-green-600 text-white text-sm font-medium hover:bg-green-500 disabled:opacity-50 transition-colors"
                >
                  <XCircle size={16} />
                  Falso Positivo
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
