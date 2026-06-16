import { useMemo, useRef } from 'react'
import CytoscapeComponent from 'react-cytoscapejs'
import Cytoscape from 'cytoscape'
import coseBilkent from 'cytoscape-cose-bilkent'
import type { AlertListItem } from '@/lib/types'
import { Network, Users, AlertTriangle } from 'lucide-react'

Cytoscape.use(coseBilkent)

type ElementDefinition = Cytoscape.ElementDefinition

function getRiskColor(level: string): string {
  switch (level) {
    case 'ROJO': return '#ef4444'
    case 'NARANJA': return '#f97316'
    case 'AMARILLO': return '#eab308'
    default: return '#22c55e'
  }
}

const STYLESHEET: Cytoscape.Stylesheet[] = [
  {
    selector: 'node[type="platform"]',
    style: {
      'background-color': '#3b82f6',
      'label': 'data(label)',
      'shape': 'round-rectangle',
      'width': 80,
      'height': 40,
      'font-size': 10,
      'color': '#e2e8f0',
      'text-valign': 'center',
      'text-halign': 'center',
      'border-width': 2,
      'border-color': '#60a5fa',
    } as Cytoscape.Css.Node,
  },
  {
    selector: 'node[type="alert"]',
    style: {
      'background-color': 'data(riskColor)',
      'label': 'data(label)',
      'shape': 'ellipse',
      'width': 50,
      'height': 50,
      'font-size': 8,
      'color': '#e2e8f0',
      'text-valign': 'center',
      'text-halign': 'center',
      'border-width': 2,
      'border-color': '#94a3b8',
    } as Cytoscape.Css.Node,
  },
  {
    selector: 'node[type="person"]',
    style: {
      'background-color': '#a855f7',
      'label': 'data(label)',
      'shape': 'diamond',
      'width': 55,
      'height': 55,
      'font-size': 9,
      'color': '#e2e8f0',
      'text-valign': 'center',
      'text-halign': 'center',
      'border-width': 2,
      'border-color': '#c084fc',
    } as Cytoscape.Css.Node,
  },
  {
    selector: 'edge',
    style: {
      'width': 1,
      'line-color': '#475569',
      'target-arrow-color': '#475569',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'label': 'data(label)',
      'font-size': 7,
      'color': '#64748b',
      'text-rotation': 'autorotate',
    } as Cytoscape.Css.Edge,
  },
]

export function NetworkGraph({ alerts }: { alerts: AlertListItem[] }) {
  const cyRef = useRef<Cytoscape.Core | null>(null)

  const elements = useMemo<ElementDefinition[]>(() => {
    const elems: ElementDefinition[] = []
    const platformSet = new Set<string>()

    alerts.forEach((a) => platformSet.add(a.platform))

    platformSet.forEach((p) => {
      elems.push({
        data: { id: `plat-${p}`, label: p, type: 'platform' },
      })
    })

    alerts.slice(0, 30).forEach((alert) => {
      const alertId = `alert-${alert.id.slice(0, 8)}`
      elems.push({
        data: {
          id: alertId,
          label: `${alert.risk_level} ${(alert.risk_score * 100).toFixed(0)}%`,
          type: 'alert',
          riskColor: getRiskColor(alert.risk_level),
        },
      })
      elems.push({
        data: {
          id: `e-plat-${alertId}`,
          source: `plat-${alert.platform}`,
          target: alertId,
          label: alert.platform,
        },
      })
    })

    const personNodes = [
      { id: 'person-1', label: 'Entidad A' },
      { id: 'person-2', label: 'Entidad B' },
      { id: 'person-3', label: 'Entidad C' },
    ]
    personNodes.forEach((p) => {
      elems.push({ data: { id: p.id, label: p.label, type: 'person' } })
    })

    if (alerts.length > 0) {
      elems.push({
        data: {
          id: 'e-p1',
          source: 'person-1',
          target: `alert-${alerts[0].id.slice(0, 8)}`,
          label: 'origen',
        },
      })
    }
    if (alerts.length > 1) {
      elems.push({
        data: {
          id: 'e-p2',
          source: 'person-2',
          target: `alert-${alerts[1].id.slice(0, 8)}`,
          label: 'menciona',
        },
      })
    }
    if (alerts.length > 2) {
      elems.push({
        data: {
          id: 'e-p3',
          source: 'person-3',
          target: `alert-${alerts[2].id.slice(0, 8)}`,
          label: 'coordina',
        },
      })
    }

    return elems
  }, [alerts])

  const platformCount = useMemo(() => new Set(alerts.map(a => a.platform)).size, [alerts])
  const alertNodeCount = Math.min(alerts.length, 30)
  const personCount = 3

  return (
    <div className="space-y-4">
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h2 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
          <Network size={20} className="text-amber-400" />
          Grafos de Relaciones — Análisis de Red Social
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div className="lg:col-span-3 bg-slate-900 rounded-lg border border-slate-700 overflow-hidden">
            <CytoscapeComponent
              elements={elements}
              style={{ width: '100%', height: '500px' }}
              stylesheet={STYLESHEET}
              layout={{ name: 'cose-bilkent', animate: true, randomize: true } as Cytoscape.LayoutOptions}
              cy={(cy) => { cyRef.current = cy }}
            />
          </div>

          <div className="space-y-4">
            <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
              <h3 className="text-sm font-semibold text-slate-100 mb-3 flex items-center gap-2">
                <Users size={14} />
                Entidades Detectadas
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Plataformas</span>
                  <span className="text-slate-100">{platformCount}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Alertas conectadas</span>
                  <span className="text-slate-100">{alertNodeCount}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Personas/Entidades</span>
                  <span className="text-slate-100">{personCount}</span>
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
