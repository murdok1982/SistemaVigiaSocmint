import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { OrchestratorResponse } from '@/lib/types'
import { CheckCircle, ChevronDown, ChevronUp, Loader2, Play, X } from 'lucide-react'

const PLATFORMS = ['twitter', 'telegram', 'facebook', 'reddit', 'web']

interface RunAnalysisModalProps {
  onClose: () => void
}

export function RunAnalysisModal({ onClose }: RunAnalysisModalProps) {
  const [objective, setObjective] = useState('')
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([])
  const [maxResults, setMaxResults] = useState(20)
  const [result, setResult] = useState<OrchestratorResponse | null>(null)
  const [showActions, setShowActions] = useState(false)

  const queryClient = useQueryClient()

  const { mutate: runAnalysis, isPending, error } = useMutation({
    mutationFn: () =>
      api.runAnalysis({
        objective: objective.trim(),
        platforms: selectedPlatforms.length > 0 ? selectedPlatforms.join(',') : undefined,
        max_results: maxResults,
      }),
    onSuccess: (data) => {
      setResult(data)
      void queryClient.invalidateQueries({ queryKey: ['alerts'] })
      void queryClient.invalidateQueries({ queryKey: ['health'] })
      void queryClient.invalidateQueries({ queryKey: ['audit-log'] })
    },
  })

  const togglePlatform = (p: string) =>
    setSelectedPlatforms((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
    )

  const canSubmit = objective.trim().length >= 5 && !isPending

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Lanzar análisis OSINT"
    >
      <div className="w-full max-w-lg rounded-xl border border-slate-700 bg-slate-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <Play size={16} className="text-amber-400" aria-hidden="true" />
            <h2 className="text-sm font-semibold text-slate-100">Lanzar análisis OSINT/SOCMINT</h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400 rounded"
            aria-label="Cerrar"
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4 space-y-4">
          {!result ? (
            <>
              <div>
                <label htmlFor="analysis-objective" className="block text-sm font-medium text-slate-300 mb-1">
                  Objetivo del análisis <span className="text-red-400" aria-hidden="true">*</span>
                </label>
                <input
                  id="analysis-objective"
                  type="text"
                  value={objective}
                  onChange={(e) => setObjective(e.target.value)}
                  placeholder="Ej: Detectar amenazas de violencia en canales públicos de Telegram"
                  className="w-full rounded-md border border-slate-600 bg-slate-800 text-slate-200 text-sm px-3 py-2 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500"
                  disabled={isPending}
                />
              </div>

              <div>
                <p className="text-sm font-medium text-slate-300 mb-2">
                  Plataformas <span className="text-xs font-normal text-slate-500">(todas si ninguna seleccionada)</span>
                </p>
                <div className="flex flex-wrap gap-2">
                  {PLATFORMS.map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => togglePlatform(p)}
                      disabled={isPending}
                      aria-pressed={selectedPlatforms.includes(p)}
                      className={[
                        'px-3 py-1.5 rounded-md text-xs font-mono font-medium border transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400 disabled:opacity-40',
                        selectedPlatforms.includes(p)
                          ? 'bg-amber-500/20 border-amber-500/50 text-amber-300'
                          : 'bg-slate-800 border-slate-600 text-slate-400 hover:bg-slate-700 hover:text-slate-200',
                      ].join(' ')}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label htmlFor="max-results" className="block text-sm font-medium text-slate-300 mb-1">
                  Máx. resultados por plataforma: <span className="text-amber-400 font-mono">{maxResults}</span>
                </label>
                <input
                  id="max-results"
                  type="range"
                  min={5}
                  max={100}
                  step={5}
                  value={maxResults}
                  onChange={(e) => setMaxResults(Number(e.target.value))}
                  disabled={isPending}
                  className="w-full accent-amber-500 disabled:opacity-40"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-0.5">
                  <span>5</span>
                  <span>100</span>
                </div>
              </div>

              {error && (
                <p className="text-sm text-red-400 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2" role="alert">
                  {(error as Error).message}
                </p>
              )}

              <div className="flex gap-3 pt-1">
                <button
                  onClick={onClose}
                  disabled={isPending}
                  className="flex-1 px-4 py-2.5 rounded-md border border-slate-600 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-40 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400"
                >
                  Cancelar
                </button>
                <button
                  onClick={() => runAnalysis()}
                  disabled={!canSubmit}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-md bg-amber-600 text-sm font-semibold text-white hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-amber-400"
                >
                  {isPending ? (
                    <>
                      <Loader2 size={16} className="animate-spin" aria-hidden="true" />
                      Analizando...
                    </>
                  ) : (
                    <>
                      <Play size={16} aria-hidden="true" />
                      Lanzar análisis
                    </>
                  )}
                </button>
              </div>
            </>
          ) : (
            <div className="space-y-4">
              <div className="flex items-start gap-3 rounded-lg border border-green-500/30 bg-green-500/10 p-3">
                <CheckCircle size={18} className="text-green-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <p className="text-sm font-semibold text-green-300">Análisis completado</p>
                  <p className="text-xs text-slate-400 mt-0.5">{result.final_recommendation}</p>
                </div>
              </div>

              <div className="rounded-lg border border-slate-700 bg-slate-800 p-3">
                <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Resumen</p>
                <p className="text-sm text-slate-300">{result.reasoning_summary}</p>
              </div>

              <button
                type="button"
                onClick={() => setShowActions(!showActions)}
                className="flex items-center gap-2 text-xs text-slate-400 hover:text-slate-200 transition-colors focus:outline-none"
              >
                {showActions ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                {showActions ? 'Ocultar' : 'Ver'} pasos del pipeline ({result.actions.length})
              </button>

              {showActions && (
                <ol className="space-y-1.5">
                  {result.actions.map((action) => (
                    <li key={action.step} className="flex items-start gap-2 text-xs">
                      <span className="font-mono bg-slate-700 text-slate-400 px-1.5 py-0.5 rounded flex-shrink-0">
                        {action.step}
                      </span>
                      <div>
                        <span className="text-amber-400 font-medium">{action.agent}</span>
                        <span className="text-slate-400 ml-1">— {action.task}</span>
                        <span className={[
                          'ml-2 text-xs font-mono',
                          action.status === 'completed' ? 'text-green-400' : 'text-slate-500',
                        ].join(' ')}>
                          [{action.status}]
                        </span>
                      </div>
                    </li>
                  ))}
                </ol>
              )}

              <button
                onClick={onClose}
                className="w-full px-4 py-2.5 rounded-md bg-slate-700 text-sm font-medium text-slate-200 hover:bg-slate-600 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400"
              >
                Cerrar y ver alertas
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
