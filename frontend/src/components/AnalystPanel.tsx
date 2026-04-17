import { useState } from 'react'
import type { ReviewAction } from '@/lib/types'
import { cn } from '@/lib/utils'
import { Archive, Loader2, ShieldAlert, XCircle } from 'lucide-react'

interface AnalystPanelProps {
  alertId: string
  onSubmit: (action: ReviewAction, notes: string, analystId: string) => Promise<void>
  isSubmitting: boolean
}

const ACTIONS = [
  {
    value: 'ESCALAR' as ReviewAction,
    label: 'Escalar',
    description: 'Remitir a autoridad competente',
    icon: <ShieldAlert size={18} />,
    className: 'border-red-500/50 bg-red-500/10 text-red-400 hover:bg-red-500/20',
    activeClassName: 'bg-red-500/30 border-red-400',
  },
  {
    value: 'ARCHIVAR' as ReviewAction,
    label: 'Archivar',
    description: 'Registrar sin acción inmediata',
    icon: <Archive size={18} />,
    className: 'border-slate-500/50 bg-slate-700/50 text-slate-300 hover:bg-slate-600/50',
    activeClassName: 'bg-slate-600 border-slate-400',
  },
  {
    value: 'FALSO_POSITIVO' as ReviewAction,
    label: 'Falso positivo',
    description: 'No representa amenaza real',
    icon: <XCircle size={18} />,
    className: 'border-green-500/50 bg-green-500/10 text-green-400 hover:bg-green-500/20',
    activeClassName: 'bg-green-500/20 border-green-400',
  },
]

export function AnalystPanel({ alertId: _alertId, onSubmit, isSubmitting }: AnalystPanelProps) {
  const [selectedAction, setSelectedAction] = useState<ReviewAction | null>(null)
  const [notes, setNotes] = useState('')
  const [analystId, setAnalystId] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!selectedAction) { setError('Debes seleccionar una acción.'); return }
    if (notes.trim().length < 10) { setError('Las notas deben tener al menos 10 caracteres.'); return }
    if (!analystId.trim()) { setError('Debes ingresar tu identificador de analista.'); return }

    await onSubmit(selectedAction, notes.trim(), analystId.trim())
  }

  return (
    <section
      className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-5"
      aria-label="Panel de decisión del analista"
    >
      <div className="flex items-center gap-2 mb-4">
        <ShieldAlert size={18} className="text-amber-400" aria-hidden="true" />
        <h2 className="text-sm font-semibold text-amber-300 uppercase tracking-wide">
          Decisión del analista — revisión humana obligatoria
        </h2>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <fieldset className="mb-4">
          <legend className="text-sm font-medium text-slate-300 mb-2">
            Acción <span className="text-red-400" aria-hidden="true">*</span>
          </legend>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {ACTIONS.map((action) => (
              <button
                key={action.value}
                type="button"
                aria-pressed={selectedAction === action.value}
                onClick={() => setSelectedAction(action.value)}
                className={cn(
                  'flex items-center gap-2.5 rounded-lg border px-3 py-2.5 text-left text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-slate-400',
                  action.className,
                  selectedAction === action.value && action.activeClassName,
                )}
              >
                <span aria-hidden="true">{action.icon}</span>
                <span>
                  <span className="block">{action.label}</span>
                  <span className="block text-xs opacity-70 font-normal">{action.description}</span>
                </span>
              </button>
            ))}
          </div>
        </fieldset>

        <div className="mb-4">
          <label htmlFor="analyst-id" className="block text-sm font-medium text-slate-300 mb-1">
            ID de analista <span className="text-red-400" aria-hidden="true">*</span>
          </label>
          <input
            id="analyst-id"
            type="text"
            value={analystId}
            onChange={(e) => setAnalystId(e.target.value)}
            placeholder="Ej: ANL-001"
            className="w-full rounded-md border border-slate-600 bg-slate-800 text-slate-200 text-sm px-3 py-2 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-400"
            required
          />
        </div>

        <div className="mb-4">
          <label htmlFor="analyst-notes" className="block text-sm font-medium text-slate-300 mb-1">
            Notas <span className="text-red-400" aria-hidden="true">*</span>
            <span className="text-xs font-normal text-slate-500 ml-2">(mínimo 10 caracteres)</span>
          </label>
          <textarea
            id="analyst-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Justificación de la decisión tomada..."
            rows={4}
            className="w-full rounded-md border border-slate-600 bg-slate-800 text-slate-200 text-sm font-mono px-3 py-2 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-400 resize-none"
            required
            minLength={10}
          />
          <p className="text-xs text-slate-500 mt-1 text-right">{notes.length} caracteres</p>
        </div>

        {error && <p className="text-sm text-red-400 mb-3" role="alert">{error}</p>}

        <button
          type="submit"
          disabled={isSubmitting || !selectedAction || notes.trim().length < 10 || !analystId.trim()}
          className="w-full flex items-center justify-center gap-2 rounded-md bg-amber-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-amber-400"
        >
          {isSubmitting && <Loader2 size={16} className="animate-spin" aria-hidden="true" />}
          {isSubmitting ? 'Registrando decisión...' : 'Confirmar decisión'}
        </button>
      </form>
    </section>
  )
}
