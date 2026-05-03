import { useMemo } from 'react'
import type { AlertListItem } from '@/lib/types'
import { Network, Users, AlertTriangle } from 'lucide-react'

// Grafo simulado
interface GraphNode {
  id: string
  label: string
  type: 'person' | 'alert' | 'platform'
  risk?: string
}

interface GraphEdge {
  source: string
  target: string
  label: string
}

export function NetworkGraph({ alerts }: { alerts: AlertListItem[] }) {
  const { nodes, edges } = useMemo(() => {
    const nodes: GraphNode[] = []
    const edges: GraphEdge[] = []

    // Nodos de plataformas
    const platforms = [...new Set(alerts.map(a => a.platform))]
    platforms.forEach(p => {
      nodes.push({ id: `plat-${p}`, label: p, type: 'platform' })
    })

    // Nodos de alertas
    alerts.slice(0, 20).forEach((alert) => {
      const alertId = `alert-${alert.id.slice(0, 8)}`
      nodes.push({
        id: alertId,
        label: `${alert.risk_level} ${(alert.risk_score * 100).toFixed(0)}%`,
        type: 'alert',
        risk: alert.risk_level,
      })
      edges.push({
        source: `plat-${alert.platform}`,
        target: alertId,
        label: alert.platform,
      })
    })

    // Nodos simulados
    nodes.push({ id: 'person-1', label: 'Entidad A', type: 'person' })
    nodes.push({ id: 'person-2', label: 'Entidad B', type: 'person' })
    edges.push({ source: 'person-1', target: 'alert-1', label: 'origen' })
    edges.push({ source: 'person-2', target: 'alert-2', label: 'menciona' })

    return { nodes, edges }
  }, [alerts])

  const getNodeColor = (type: string, risk?: string) => {
    if (type === 'platform') return 'bg-blue-500/20 text-blue-400 border-blue-500'
    if (type === 'person') return 'bg-purple-500/20 text-purple-400 border-purple-500'
    if (risk === 'ROJO') return 'bg-red-500/20 text-red-400 border-red-500'
    if (risk === 'NARANJA') return 'bg-orange-500/20 text-orange-400 border-orange-500'
    return 'bg-yellow-500/20 text-yellow-400 border-yellow-500'
  }

  return (
    <div className="space-y-4">
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h2 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
          <Network size={20} className="text-amber-400" />
          Grafos de Relaciones — Análisis de Red Social
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Visualización del grafo */}
          <div className="lg:col-span-3 bg-slate-900 rounded-lg h-96 border border-slate-700 p-4 overflow-auto">
            <div className="text-center mb-4">
              <p className="text-slate-500 text-sm">Visualización de Grafos (Cytoscape.js/D3.js pendiente)</p>
            </div>

            <div className="space-y-2">
              {nodes.map((node) => (
                <span
                  key={node.id}
                  className={`inline-block px-3 py-1.5 rounded-full text-xs font-medium border ${getNodeColor(node.type, node.risk)} mr-2 mb-2`}
                >
                  {node.label}
                </span>
              ))}
            </div>

            <div className="mt-4 space-y-1">
              <p className="text-xs text-slate-500 mb-2">Conexiones detectadas:</p>
              {edges.map((edge, idx) => (
                <div key={idx} className="text-xs text-slate-400">
                  <span className="text-slate-300">{edge.source}</span>
                  <span className="mx-2">→</span>
                  <span className="text-slate-300">{edge.target}</span>
                  <span className="text-slate-500 ml-2">({edge.label})</span>
                </div>
              ))}
            </div>
          </div>

          {/* Panel de control */}
          <div className="space-y-4">
            <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
              <h3 className="text-sm font-semibold text-slate-100 mb-3 flex items-center gap-2">
                <Users size={14} />
                Entidades Detectadas
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Plataformas</span>
                  <span className="text-slate-100">{nodes.filter(n => n.type === 'platform').length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Alertas conectadas</span>
                  <span className="text-slate-100">{nodes.filter(n => n.type === 'alert').length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Personas/Entidades</span>
                  <span className="text-slate-100">{nodes.filter(n => n.type === 'person').length}</span>
                </div>
              </div>
            </div>

            <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
              <h3 className="text-sm font-semibold text-slate-100 mb-3 flex items-center gap-2">
                <AlertTriangle size={14} />
                Tipos de Conexión
              </h3>
              <div className="space-y-1 text-xs text-slate-400">
                <p>• origen (fuente → alerta)</p>
                <p>• menciona (entidad → alerta)</p>
                <p>• comparte (alerta → alerta)</p>
                <p>• coordina (persona → persona)</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
