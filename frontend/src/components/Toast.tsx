import { useEffect } from 'react'
import { X } from 'lucide-react'

interface Props {
  message: string
  type: 'success' | 'error' | 'info'
  onClose: () => void
  visible: boolean
}

const TYPE_STYLES: Record<string, string> = {
  success: 'border-green-500/50 text-green-400',
  error: 'border-red-500/50 text-red-400',
  info: 'border-blue-500/50 text-blue-400',
}

export function Toast({ message, type, onClose, visible }: Props) {
  useEffect(() => {
    if (!visible) return
    const t = setTimeout(onClose, 5000)
    return () => clearTimeout(t)
  }, [visible, onClose])

  if (!visible) return null

  return (
    <div
      className="fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg border bg-slate-800 shadow-lg"
      role="alert"
    >
      <span className={`text-sm font-medium ${TYPE_STYLES[type]}`}>{message}</span>
      <button
        onClick={onClose}
        className="text-slate-400 hover:text-slate-200 transition-colors"
        aria-label="Cerrar notificación"
      >
        <X size={14} />
      </button>
    </div>
  )
}
