import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Toast } from '@/components/Toast'
import { UserPlus } from 'lucide-react'

export function AdminPage() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('analyst')
  const [clearanceLevel, setClearanceLevel] = useState('CONFIDENTIAL')
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info'; visible: boolean }>({
    message: '',
    type: 'info',
    visible: false,
  })

  const mutation = useMutation({
    mutationFn: () =>
      api.createAnalyst({
        username,
        email,
        full_name: fullName,
        password,
        role,
        clearance_level: clearanceLevel,
      }),
    onSuccess: (data) => {
      setToast({ message: data.message || 'Analista creado correctamente', type: 'success', visible: true })
      setUsername('')
      setEmail('')
      setFullName('')
      setPassword('')
      setRole('analyst')
      setClearanceLevel('CONFIDENTIAL')
    },
    onError: (err: Error) => {
      setToast({ message: err.message || 'Error al crear analista', type: 'error', visible: true })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!username || !email || !fullName || !password) {
      setToast({ message: 'Todos los campos son obligatorios', type: 'error', visible: true })
      return
    }
    mutation.mutate()
  }

  return (
    <main className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100">Administración de Analistas</h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Gestión de cuentas y permisos del equipo de análisis
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-slate-800 p-6 rounded-lg border border-slate-700 space-y-5 max-w-xl"
      >
        <div>
          <label htmlFor="admin-username" className="block text-xs text-slate-400 mb-1">
            Nombre de Usuario
          </label>
          <input
            id="admin-username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Ej: jgarcia"
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
          />
        </div>

        <div>
          <label htmlFor="admin-email" className="block text-xs text-slate-400 mb-1">
            Correo Electrónico
          </label>
          <input
            id="admin-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Ej: jgarcia@vigia.mil"
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
          />
        </div>

        <div>
          <label htmlFor="admin-fullname" className="block text-xs text-slate-400 mb-1">
            Nombre Completo
          </label>
          <input
            id="admin-fullname"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Ej: Juan García López"
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
          />
        </div>

        <div>
          <label htmlFor="admin-password" className="block text-xs text-slate-400 mb-1">
            Contraseña
          </label>
          <input
            id="admin-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Mínimo 12 caracteres"
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="admin-role" className="block text-xs text-slate-400 mb-1">
              Rol
            </label>
            <select
              id="admin-role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-amber-500"
            >
              <option value="analyst">Analyst</option>
              <option value="supervisor">Supervisor</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div>
            <label htmlFor="admin-clearance" className="block text-xs text-slate-400 mb-1">
              Nivel de Clearance
            </label>
            <select
              id="admin-clearance"
              value={clearanceLevel}
              onChange={(e) => setClearanceLevel(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-amber-500"
            >
              <option value="CONFIDENTIAL">CONFIDENTIAL</option>
              <option value="SECRET">SECRET</option>
              <option value="TOP_SECRET">TOP_SECRET</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={mutation.isPending}
          className="flex items-center gap-2 px-5 py-2.5 rounded-md bg-amber-600 text-sm font-semibold text-white hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-amber-400"
        >
          <UserPlus size={15} aria-hidden="true" />
          {mutation.isPending ? 'Creando...' : 'Crear Analista'}
        </button>
      </form>

      <Toast
        message={toast.message}
        type={toast.type}
        visible={toast.visible}
        onClose={() => setToast((t) => ({ ...t, visible: false }))}
      />
    </main>
  )
}
