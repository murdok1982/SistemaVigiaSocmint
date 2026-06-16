import { useMemo, useRef } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import type { AlertListItem } from '@/lib/types'
import { MapPin, Shield, TrendingUp, Crosshair, AlertTriangle, Clock, CheckCircle } from 'lucide-react'

function hashString(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

function getCoordsForAlert(alert: AlertListItem): [number, number] {
  const baseLat = 40.4168
  const baseLng = -3.7038
  const h = hashString(alert.id + alert.platform)
  const latOffset = ((h % 1000) / 1000 - 0.5) * 8
  const lngOffset = (((h >> 10) % 1000) / 1000 - 0.5) * 10
  return [baseLat + latOffset, baseLng + lngOffset]
}

function getRiskColorHex(level: string): string {
  switch (level) {
    case 'ROJO': return '#ef4444'
    case 'NARANJA': return '#f97316'
    case 'AMARILLO': return '#eab308'
    default: return '#22c55e'
  }
}

function getRiskColor(level: string): string {
  switch (level) {
    case 'ROJO': return 'text-red-500 bg-red-500/20 border-red-500'
    case 'NARANJA': return 'text-orange-500 bg-orange-500/20 border-orange-500'
    case 'AMARILLO': return 'text-yellow-500 bg-yellow-500/20 border-yellow-500'
    default: return 'text-green-500 bg-green-500/20 border-green-500'
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'PENDIENTE': return <Clock size={12} className="text-yellow-400 inline mr-1" />
    case 'ESCALADA': return <AlertTriangle size={12} className="text-red-400 inline mr-1" />
    case 'ARCHIVADA': return <Shield size={12} className="text-slate-400 inline mr-1" />
    case 'FALSO_POSITIVO': return <CheckCircle size={12} className="text-green-400 inline mr-1" />
    default: return null
  }
}

function CenterMapButton() {
  const map = useMap()
  return (
    <button
      onClick={() => map.setView([40.4168, -3.7038], 6)}
      className="absolute top-3 right-3 z-[1000] flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-md text-xs text-slate-300 hover:bg-slate-700 transition-colors shadow-lg"
      aria-label="Centrar mapa"
    >
      <Crosshair size={14} />
      Centrar
    </button>
  )
}

const LEGEND_ITEMS = [
  { level: 'ROJO', color: '#ef4444', label: 'Crítico' },
  { level: 'NARANJA', color: '#f97316', label: 'Alto' },
  { level: 'AMARILLO', color: '#eab308', label: 'Medio' },
  { level: 'VERDE', color: '#22c55e', label: 'Bajo' },
]

export function MapView({ alerts }: { alerts: AlertListItem[] }) {
  const mapRef = useRef(null)

  const alertsByLocation = useMemo(() => {
    const grouped: Record<string, { city: string; count: number; alerts: AlertListItem[] }> = {}
    alerts.forEach((alert) => {
      const [lat, lng] = getCoordsForAlert(alert)
      const cityKey = `${Math.round(lat)},${Math.round(lng)}`
      if (!grouped[cityKey]) {
        grouped[cityKey] = { city: `${lat.toFixed(2)}, ${lng.toFixed(2)}`, count: 0, alerts: [] }
      }
      grouped[cityKey].count++
      grouped[cityKey].alerts.push(alert)
    })
    return Object.values(grouped)
  }, [alerts])

  return (
    <div className="space-y-4">
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <MapPin size={20} className="text-amber-400" />
            Mapa Táctico — Distribución Geográfica de Alertas
          </h2>
          <div className="flex items-center gap-3">
            {LEGEND_ITEMS.map(({ color, label }) => (
              <div key={label} className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-xs text-slate-400">{label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="relative">
          <MapContainer
            {...{
              center: [40.4168, -3.7038],
              zoom: 6,
              style: { height: '500px', width: '100%', borderRadius: '0.5rem' },
              scrollWheelZoom: true,
              ref: mapRef,
            }}
          >
            <TileLayer
              {...{
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
              }}
            />
            <CenterMapButton />
            {alerts.map((alert) => {
              const [lat, lng] = getCoordsForAlert(alert)
              return (
                <CircleMarker
                  key={alert.id}
                  {...{
                    center: [lat, lng] as [number, number],
                    radius: 8,
                    pathOptions: {
                      color: getRiskColorHex(alert.risk_level),
                      fillColor: getRiskColorHex(alert.risk_level),
                      fillOpacity: 0.6,
                      weight: 2,
                    },
                  }}
                >
                  <Popup>
                    <div className="text-sm min-w-[180px]">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-slate-900">{alert.risk_level}</span>
                        <span className="text-xs font-semibold text-slate-600">{(alert.risk_score * 100).toFixed(0)}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden mb-2">
                        <div
                          className="h-full rounded-full"
                          style={{ width: `${alert.risk_score * 100}%`, backgroundColor: getRiskColorHex(alert.risk_level) }}
                        />
                      </div>
                      <p className="text-xs text-slate-500 mb-1">{alert.platform}</p>
                      <p className="text-xs text-slate-700 mb-2">{alert.content_excerpt.slice(0, 120)}</p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-500">
                          {getStatusIcon(alert.status)}{alert.status}
                        </span>
                        <span className="text-xs text-slate-400">
                          {alert.indicators.length} indicador{alert.indicators.length !== 1 ? 'es' : ''}
                        </span>
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              )
            })}
          </MapContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {alertsByLocation.map((loc) => (
          <div key={loc.city} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-slate-100 text-sm">{loc.city}</h3>
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

      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <h3 className="text-sm font-semibold text-slate-100 mb-3 flex items-center gap-2">
          <TrendingUp size={16} className="text-green-400" />
          Tendencia Temporal (Últimas 24h)
        </h3>
        <div className="h-32 bg-slate-900 rounded flex items-center justify-center">
          <p className="text-slate-500 text-sm">Gráfico de tendencia temporal (pendiente)</p>
        </div>
      </div>
    </div>
  )
}
