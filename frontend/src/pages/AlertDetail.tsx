import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { useAuth } from '@/lib/AuthContext'
import { ArrowLeft, Shield, AlertTriangle, XCircle, Archive, Send, Globe, Hash, AtSign, Link2, FileText, HelpCircle, X } from 'lucide-react'
import type { ReviewRequest } from '@/lib/types'
import { useState } from 'react'

function getIndicatorIcon(type: string) {
  const t = type.toUpperCase()
  if (t.includes('URL') || t.includes('LINK')) return <Link2 size={14} className="text-blue-400" />
  if (t.includes('IP') || t.includes('HOST')) return <Globe size={14} className="text-purple-400" />
  if (t.includes('EMAIL') || t.includes('MAIL')) return <AtSign size={14} className="text-cyan-400" />
  if (t.includes('HASH') || t.includes('MD5') || t.includes('SHA')) return <Hash size={14} className="text-pink-400" />
  if (t.includes('KEYWORD') || t.includes('TEXT') || t.includes('CONTENT')) return <FileText size={14} className="text-amber-400" />
  return <HelpCircle size={14} className="text-slate-400" />
}

function getRiskBarColor(score: number) {
  if (score >= 0.75) return 'bg-red-500'
  if (score >= 0.5) return 'bg-orange-500'
  if (score >= 0.25) return 'bg-yellow-500'
  return 'bg-green-500'
}

function getRiskBarLabel(score: number) {
  if (score >= 0.75) return 'Crítico'
  if (score >= 0.5) return 'Alto'
  if (score >= 0.25) return 'Medio'
  return 'Bajo'
}

export function AlertDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [notes, setNotes] = useState('')
  const [confirmAction, setConfirmAction] = useState<'ESCALAR' | 'ARCHIVAR' | 'FALSO_POSITIVO' | null>(null)

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

  const handleReview = (selectedAction: 'ESCALAR' | 'ARCHIVAR' | 'FALSO_POSITIVO') => {
    if (!notes || notes.length < 10) return
    setConfirmAction(selectedAction)
  }

  const confirmReview = () => {
    if (!confirmAction) return
    reviewMutation.mutate({
      action: confirmAction,
      notes,
      analyst_id: user?.sub || user?.username || 'unknown',
    })
    setConfirmAction(null)
  }

  if (isLoading) return <div className="p-6 text-slate-400">Cargando detalles...</div>
  if (isError || !alert) return <div className="p-6 text-red-400">Error cargando la alerta</div>

  const riskPercent = Math.round(alert.risk_score * 100)

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'ROJO': return 'text-red-400 bg-red-500/20 border-red-500'
      case 'NARANJA': return 'text-orange-400 bg-orange-500/20 border-orange-500'
      case 'AMARILLO': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500'
      default: return 'text-green-400 bg-green-500/20 border-green-500'
    }
  }

  const actionLabels: Record<string, string> = {
    ESCALAR: 'Escalar alerta',
    ARCHIVAR: 'Archivar alerta',
    FALSO_POSITIVO: 'Marcar como falso positivo',
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
        <div className={`p-6 border-b border-slate-700 ${getRiskColor(alert.risk_level)} border-l-4`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Shield size={24} className={getRiskColor(alert.risk_level).split(' ')[0]} />
              <div>
                <h1 className="text-2xl font-bold text-slate-100">{alert.risk_level}</h1>
                <p className="text-sm text-slate-400">{alert.platform} • {riskPercent}% de riesgo</p>
              </div>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(alert.risk_level)}`}>
              {alert.status}
            </span>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Risk Score</span>
              <span className="font-semibold text-slate-200">{riskPercent}% — {getRiskBarLabel(alert.risk_score)}</span>
            </div>
            <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${getRiskBarColor(alert.risk_score)}`}
                style={{ width: `${riskPercent}%` }}
                role="progressbar"
                aria-valuenow={riskPercent}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Puntuación de riesgo: ${riskPercent}%`}
              />
            </div>
          </div>
        </div>

        <div className="p-6 space-y-6">
          <div>
            <h2 className="text-sm font-semibold text-slate-300 mb-2">Contenido Completo</h2>
            <div className="bg-slate-900 p-4 rounded-lg border border-slate-700">
              <p className="text-slate-200 leading-relaxed">{alert.content_full}</p>
            </div>
          </div>

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
                      <span className="flex items-center gap-1.5 text-xs font-medium text-amber-400">
                        {getIndicatorIcon(ind.type)}
                        {ind.type}
                      </span>
                      <span className="text-xs text-slate-500">Confianza: {(ind.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-sm text-slate-300">{ind.value}</p>
                    <p className="text-xs text-slate-400 mt-1">{ind.explanation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

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

          {alert.analyst_notes && (
            <div>
              <h2 className="text-sm font-semibold text-slate-300 mb-2">Notas del Analista</h2>
              <div className="bg-slate-900 p-4 rounded-lg border border-slate-700">
                <p className="text-slate-300">{alert.analyst_notes}</p>
              </div>
            </div>
          )}
        </div>

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
                  onClick={() => handleReview('ESCALAR')}
                  disabled={!notes || notes.length < 10 || reviewMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 rounded-md bg-red-600 text-white text-sm font-medium hover:bg-red-500 disabled:opacity-50 transition-colors"
                >
                  <Send size={16} />
                  Escalar
                </button>
                <button
                  onClick={() => handleReview('ARCHIVAR')}
                  disabled={!notes || notes.length < 10 || reviewMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 rounded-md bg-slate-600 text-white text-sm font-medium hover:bg-slate-500 disabled:opacity-50 transition-colors"
                >
                  <Archive size={16} />
                  Archivar
                </button>
                <button
                  onClick={() => handleReview('FALSO_POSITIVO')}
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

      {confirmAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 max-w-sm w-full mx-4 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 id="confirm-title" className="text-lg font-semibold text-slate-100">Confirmar acción</h3>
              <button
                onClick={() => setConfirmAction(null)}
                className="text-slate-400 hover:text-slate-200 transition-colors"
                aria-label="Cerrar"
              >
                <X size={18} />
              </button>
            </div>
            <p className="text-sm text-slate-300 mb-2">
              ¿Está seguro de que desea <strong>{actionLabels[confirmAction].toLowerCase()}</strong>?
            </p>
            <p className="text-xs text-slate-500 mb-6">Esta acción quedará registrada en el log de auditoría.</p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setConfirmAction(null)}
                className="px-4 py-2 rounded-md bg-slate-700 text-slate-300 text-sm font-medium hover:bg-slate-600 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={confirmReview}
                disabled={reviewMutation.isPending}
                className={`px-4 py-2 rounded-md text-white text-sm font-medium transition-colors disabled:opacity-50 ${
                  confirmAction === 'ESCALAR' ? 'bg-red-600 hover:bg-red-500' :
                  confirmAction === 'FALSO_POSITIVO' ? 'bg-green-600 hover:bg-green-500' :
                  'bg-slate-600 hover:bg-slate-500'
                }`}
              >
                {reviewMutation.isPending ? 'Procesando...' : 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
