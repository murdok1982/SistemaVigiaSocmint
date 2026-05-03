import { useState } from 'react'
import { X, Play, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'

interface Props {
  onClose: () => void
}

export function RunAnalysisModal({ onClose }: Props) {
  const [objective, setObjective] = useState('')
  const [platforms, setPlatforms] = useState<string[]>([])
  const [maxResults, setMaxResults] = useState(50)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState('')

  const availablePlatforms = [
    { id: 'twitter', label: 'Twitter/X' },
    { id: 'reddit', label: 'Reddit' },
    { id: 'telegram', label: 'Telegram' },
    { id: 'facebook', label: 'Facebook' },
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!objective.trim() || objective.length < 5) return

    setIsRunning(true)
    setError('')

    try {
      await api.runAnalysis({
        objective,
        platforms: platforms.join(','),
        max_results: maxResults,
      })
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error lanzando análisis')
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-lg border border-slate-700 w-full max-w-md">
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-slate-100">Lanzar Análisis OSINT</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Objetivo del Análisis
            </label>
            <textarea
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              placeholder="Ej: Monitoreo de amenazas violentas en redes sociales..."
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-slate-100 text-sm placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500"
              rows={3}
              minLength={5}
              maxLength={500}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Plataformas
            </label>
            <div className="space-y-2">
              {availablePlatforms.map((platform) => (
                <label key={platform.id} className="flex items-center gap-2 text-sm text-slate-300">
                  <input
                    type="checkbox"
                    checked={platforms.includes(platform.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setPlatforms([...platforms, platform.id])
                      } else {
                        setPlatforms(platforms.filter((p) => p !== platform.id))
                      }
                    }}
                    className="rounded border-slate-600 bg-slate-900 text-amber-600 focus:ring-amber-500"
                  />
                  {platform.label}
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Máximo de Resultados: {maxResults}
            </label>
            <input
              type="range"
              min={10}
              max={1000}
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              className="w-full"
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 text-sm text-red-400 bg-red-500/10 p-3 rounded-md">
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          <div className="flex gap-2 justify-end pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-slate-400 hover:text-slate-200 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isRunning || !objective.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white text-sm font-medium rounded-md hover:bg-amber-500 disabled:opacity-50 transition-colors"
            >
              {isRunning ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Ejecutando...
                </>
              ) : (
                <>
                  <Play size={16} />
                  Lanzar
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
