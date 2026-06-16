export type Lang = 'es' | 'en'
const translations: Record<Lang, Record<string, string>> = {
  es: {
    'nav.dashboard': 'Dashboard',
    'nav.audit': 'Auditoría',
    'nav.admin': 'Administración',
    'nav.logout': 'Cerrar sesión',
    'login.title': 'Iniciar sesión',
    'login.username': 'Usuario',
    'login.password': 'Contraseña',
    'login.submit': 'Acceder',
    'login.mfa.title': 'Verificación en dos pasos',
    'login.mfa.label': 'Código TOTP',
    'login.mfa.submit': 'Validar código',
    'dashboard.title': 'Centro de Monitoreo Táctico',
    'dashboard.subtitle': 'Sistema VIGÍA — Nivel: ESTATAL-MILITAR — Revisión humana obligatoria',
    'dashboard.run_analysis': 'Lanzar Análisis',
    'dashboard.export': 'Exportar',
    'alerts.queue': 'Cola de Alertas',
    'alerts.map': 'Mapa Táctico',
    'alerts.network': 'Grafos de Red',
    'alerts.reports': 'Informes',
    'audit.title': 'Log de Auditoría',
    'audit.subtitle': 'Registro inmutable de todas las acciones del sistema',
  },
  en: {
    'nav.dashboard': 'Dashboard',
    'nav.audit': 'Audit',
    'nav.admin': 'Administration',
    'nav.logout': 'Sign out',
    'login.title': 'Sign in',
    'login.username': 'Username',
    'login.password': 'Password',
    'login.submit': 'Sign in',
    'login.mfa.title': 'Two-factor authentication',
    'login.mfa.label': 'TOTP Code',
    'login.mfa.submit': 'Verify code',
    'dashboard.title': 'Tactical Monitoring Center',
    'dashboard.subtitle': 'VIGÍA System — State-Military Level — Mandatory human review',
    'dashboard.run_analysis': 'Run Analysis',
    'dashboard.export': 'Export',
    'alerts.queue': 'Alert Queue',
    'alerts.map': 'Tactical Map',
    'alerts.network': 'Network Graphs',
    'alerts.reports': 'Reports',
    'audit.title': 'Audit Log',
    'audit.subtitle': 'Immutable record of all system actions',
  },
}
let currentLang: Lang = (localStorage.getItem('vigia-lang') as Lang) || 'es'
export function t(key: string): string {
  return translations[currentLang]?.[key] ?? key
}
export function setLang(lang: Lang) {
  currentLang = lang
  localStorage.setItem('vigia-lang', lang)
  window.dispatchEvent(new CustomEvent('vigia-lang-change'))
}
export function getLang(): Lang { return currentLang }
