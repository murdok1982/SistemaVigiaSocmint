import { useMemo } from 'react'
import type { AlertListItem } from '@/lib/types'
import { MapPin, AlertTriangle, Shield, TrendingUp } from 'lucide-react'

// Coordenadas simuladas para demostración
const SIMULATED_LOCATIONS: Record<string, { lat: number; lng: number; city: string }> = {
  'twitter': { lat: 40.4168, lng: -3.7038, city: 'Madrid' },
  'telegram': { lat: 41.3851, lng: 2.1734, city: 'Barcelona' },
  'reddit': { lat: 37.3891, lng: -5.9845, city: 'Sevilla' },
  'facebook': { lat: 39.4699, lng: -0.3763, city: 'Valencia' },
}

function getRiskColor(level: string): string {
  switch (level) {
    case 'ROJO': return 'text-red-500 bg-red-500/20 border-red-500'
    case 'NARANJA': return 'text-orange-500 bg-orange-500/20 border-orange-500'
    case 'AMARILLO': return 'text-yellow-500 bg-yellow-500/20 border-yellow-500'
    default: return 'text-green-500 bg-green-500/20 border-green-500'
  }
}

export function MapView({ alerts }: { alerts: AlertListItem[] }) {
  const alertsByLocation = useMemo(() => {
    const grouped: Record<string, { city: string; count: number; alerts: AlertListItem[] }> = {}
    alerts.forEach((alert) => {
      const location = SIMULATED_LOCATIONS[alert.platform.toLowerCase()] || SIMULATED_LOCATIONS['twitter']!
      if (!grouped[location.city]) {
        grouped[location.city] = { city: location.city, count: 0, alerts: [] }
      }
      grouped[location.city].count++
      grouped[location.city].alerts.push(alert)
    })
    return Object.values(grouped)
  }, [alerts])

  return (
    <div className="space-y-4">
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h2 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
          <MapPin size={20} className="text-amber-400" />
          Mapa de Calor Táctico — Distribución Geográfica de Alertas
        </h2>

        {/* Mapa simulado */}
        <div className="relative bg-slate-900 rounded-lg h-96 border border-slate-700 overflow-hidden">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <MapPin size={48} className="text-slate-600 mx-auto mb-2" />
              <p className="text-slate-500">Mapa interactivo (Integración Mapbox/Leaflet pendiente)</p>
              <p className="text-xs text-slate-600 mt-1">Coordenadas simuladas para demostración</p>
            </div>
          </div>

          {/* Pines simulados */}
          {alertsByLocation.map((loc, idx) => (
            <div
              key={loc.city}
              className="absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer group"
              style={{
                left: `${30 + idx * 20}%`,
                top: `${40 + (idx % 2) * 20}%`,
              }}
            >
              <div className="relative">
                <MapPin size={24} className="text-red-500 animate-pulse" />
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-slate-900 p-2 rounded shadow-lg border border-slate-700 z-10 min-w-[200px]">
                  <p className="text-sm font-semibold text-slate-100">{loc.city}</p>
                  <p className="text-xs text-slate-400">{loc.count} alertas activas</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Resumen por ubicación */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {alertsByLocation.map((loc) => (
          <div key={loc.city} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-slate-100">{loc.city}</h3>
              <Shield size={16} className="text-slate-400" />
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Total Alertas</span>
                <span className="text-slate-100 font-semibold">{loc.count}</span>
              </div>
              {['ROJO', 'NARANJA', 'AMARILLO', 'VERDE'].map((level) => {
                const count = loc.alerts.filter(a => a.risk_level === level).length
                if (count === 0) return null
                return (
                  <div key={level} className="flex justify-between text-sm">
                    <span className={`px-2 py-0.5 rounded text-xs ${getRiskColor(level)}`}>{level}</span>
                    <span className="text-slate-300">{count}</span>
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Métricas de tendencia */}
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <h3 className="text-sm font-semibold text-slate-100 mb-3 flex items-center gap-2">
          <TrendingUp size={16} className="text-green-400" />
          Tendencia Temporal (Últimas 24h)
        </h3>
        <div className="h-32 bg-slate-900 rounded flex items-center justify-center">
          <p className="text-slate-500 text-sm">Gráfico de tendencia temporal (Chart.js/Recharts pendiente)</p>
        </div>
      </div>
    </div>
  )
}
