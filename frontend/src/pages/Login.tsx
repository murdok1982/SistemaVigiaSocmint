import { useState, useMemo, type FormEvent } from 'react'
import { Shield, KeyRound, User, Lock, AlertCircle, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '@/lib/AuthContext'
import { MfaRequiredError } from '@/lib/auth'

type Step = 'credentials' | 'mfa'

function getPasswordStrength(pw: string): { score: number; label: string; color: string } {
  if (!pw) return { score: 0, label: '', color: 'bg-slate-700' }
  let score = 0
  if (pw.length >= 6) score++
  if (pw.length >= 10) score++
  if (/[A-Z]/.test(pw)) score++
  if (/[0-9]/.test(pw)) score++
  if (/[^A-Za-z0-9]/.test(pw)) score++
  const pct = Math.min(100, (score / 5) * 100)
  if (pct <= 20) return { score: pct, label: 'Muy débil', color: 'bg-red-500' }
  if (pct <= 40) return { score: pct, label: 'Débil', color: 'bg-orange-500' }
  if (pct <= 60) return { score: pct, label: 'Aceptable', color: 'bg-yellow-500' }
  if (pct <= 80) return { score: pct, label: 'Fuerte', color: 'bg-green-500' }
  return { score: pct, label: 'Muy fuerte', color: 'bg-emerald-400' }
}

export function Login() {
  const { login } = useAuth()
  const [step, setStep] = useState<Step>('credentials')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [mfaToken, setMfaToken] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const pwStrength = useMemo(() => getPasswordStrength(password), [password])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login({
        username: username.trim(),
        password,
        mfa_token: step === 'mfa' ? mfaToken.trim() : undefined,
      })
    } catch (err) {
      if (err instanceof MfaRequiredError) {
        setStep('mfa')
        setError('Introduce el código TOTP de tu autenticador.')
      } else {
        const message = err instanceof Error ? err.message : 'Error de autenticación'
        setError(message)
      }
    } finally {
      setSubmitting(false)
    }
  }

  function handleBackToCredentials() {
    setStep('credentials')
    setMfaToken('')
    setError(null)
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-900 text-slate-100 px-4">
      <div className="w-full max-w-md">
        <div className="flex items-center gap-3 mb-8 justify-center">
          <Shield size={28} className="text-amber-400" aria-hidden="true" />
          <div>
            <h1 className="text-xl font-bold tracking-wide">VIGÍA Monitor</h1>
            <p className="text-xs text-slate-400">Acceso restringido — Personal autorizado</p>
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-slate-800 border border-slate-700 rounded-lg p-6 space-y-4 shadow-xl"
          aria-labelledby="login-title"
          noValidate
        >
          <h2 id="login-title" className="text-lg font-semibold">
            {step === 'credentials' ? 'Iniciar sesión' : 'Verificación en dos pasos'}
          </h2>

          <div className={`transition-opacity duration-200 ${step === 'credentials' ? 'opacity-100' : 'hidden opacity-0'}`}>
            {step === 'credentials' && (
              <div className="space-y-4">
                <div>
                  <label
                    htmlFor="username"
                    className="block text-sm font-medium text-slate-300 mb-1"
                  >
                    Usuario
                  </label>
                  <div className="relative">
                    <User
                      size={16}
                      className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
                      aria-hidden="true"
                    />
                    <input
                      id="username"
                      name="username"
                      type="text"
                      autoComplete="username"
                      required
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                      disabled={submitting}
                    />
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="password"
                    className="block text-sm font-medium text-slate-300 mb-1"
                  >
                    Contraseña
                  </label>
                  <div className="relative">
                    <Lock
                      size={16}
                      className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
                      aria-hidden="true"
                    />
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      autoComplete="current-password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full pl-9 pr-10 py-2 bg-slate-900 border border-slate-700 rounded-md text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                      disabled={submitting}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                      aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                      tabIndex={-1}
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                  {password && (
                    <div className="mt-2 space-y-1">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-300 ${pwStrength.color}`}
                            style={{ width: `${pwStrength.score}%` }}
                          />
                        </div>
                        <span className={`text-xs font-medium ${pwStrength.color.replace('bg-', 'text-')}`}>
                          {pwStrength.label}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className={`transition-opacity duration-200 ${step === 'mfa' ? 'opacity-100' : 'hidden opacity-0'}`}>
            {step === 'mfa' && (
              <div>
                <p className="text-sm text-slate-300 mb-3">
                  Introduce el código de 6 dígitos de tu aplicación autenticadora
                  (Google Authenticator, Authy, etc.).
                </p>
                <label
                  htmlFor="mfa-token"
                  className="block text-sm font-medium text-slate-300 mb-1"
                >
                  Código TOTP
                </label>
                <div className="relative">
                  <KeyRound
                    size={16}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
                    aria-hidden="true"
                  />
                  <input
                    id="mfa-token"
                    name="mfa-token"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]{6}"
                    autoComplete="one-time-code"
                    required
                    maxLength={6}
                    value={mfaToken}
                    onChange={(e) => setMfaToken(e.target.value.replace(/\D/g, ''))}
                    className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-slate-100 text-sm tracking-widest focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                    disabled={submitting}
                    autoFocus
                  />
                </div>
                <button
                  type="button"
                  onClick={handleBackToCredentials}
                  className="mt-2 text-xs text-slate-400 hover:text-slate-200 transition-colors"
                  disabled={submitting}
                >
                  ← Volver a credenciales
                </button>
              </div>
            )}
          </div>

          {error && (
            <div
              role="alert"
              className="flex items-start gap-2 p-3 rounded-md bg-red-500/10 border border-red-500/40 text-red-300 text-sm"
            >
              <AlertCircle size={16} className="flex-shrink-0 mt-0.5" aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-md bg-amber-600 text-sm font-semibold text-white hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-amber-400"
          >
            {submitting ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Verificando…
              </>
            ) : step === 'credentials' ? (
              'Acceder'
            ) : (
              'Validar código'
            )}
          </button>

          <p className="text-xs text-slate-500 leading-relaxed pt-2 border-t border-slate-700">
            Toda actividad queda registrada para auditoría. El uso indebido es un delito tipificado.
          </p>
        </form>
      </div>
    </main>
  )
}
