import { useState } from 'react'
import { FileText, Download, Shield, Calendar, Mail } from 'lucide-react'
import type { AlertListItem } from '@/lib/types'

export function ReportGenerator() {
  const [reportType, setReportType] = useState<'daily' | 'weekly' | 'custom'>('daily')
  const [dateRange, setDateRange] = useState({ start: '', end: '' })
  const [generating, setGenerating] = useState(false)

  const handleGenerate = async () => {
    setGenerating(true)
    await new Promise(resolve => setTimeout(resolve, 2000))
    setGenerating(false)
    alert('Informe generado (Integración con backend pendiente)')
  }

  return (
    <div className="space-y-4">
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h2 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
          <FileText size={20} className="text-amber-400" />
          Generador de Informes Tácticos
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Configuración */}
          <div className="lg:col-span-2 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Tipo de Informe</label>
              <div className="flex gap-2">
                {(['daily', 'weekly', 'custom'] as const).map((type) => (
                  <button
                    key={type}
                    onClick={() => setReportType(type)}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      reportType === type
                        ? 'bg-amber-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {type === 'daily' && 'Diario'}
                    {type === 'weekly' && 'Semanal'}
                    {type === 'custom' && 'Personalizado'}
                  </button>
                ))}
              </div>
            </div>

            {reportType === 'custom' && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Fecha Inicio</label>
                  <input
                    type="date"
                    value={dateRange.start}
                    onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-slate-100 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Fecha Fin</label>
                  <input
                    type="date"
                    value={dateRange.end}
                    onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md text-slate-100 text-sm"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Formato de Exportación</label>
              <div className="flex gap-2">
                {['PDF', 'STIX', 'JSON', 'CSV'].map((format) => (
                  <span
                    key={format}
                    className="px-3 py-1.5 rounded-md text-xs font-medium bg-slate-700 text-slate-300 border border-slate-600"
                  >
                    {format}
                  </span>
                ))}
              </div>
            </div>

            <div className="flex gap-2 pt-4">
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="flex items-center gap-2 px-6 py-2.5 rounded-md bg-amber-600 text-sm font-semibold text-white hover:bg-amber-500 disabled:opacity-50 transition-colors"
              >
                {generating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Generando...
                  </>
                ) : (
                  <>
                    <Download size={16} />
                    Generar Informe
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Opciones adicionales */}
          <div className="space-y-4">
            <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
              <h3 className="text-sm font-semibold text-slate-100 mb-3 flex items-center gap-2">
                <Shield size={14} />
                Clasificación
              </h3>
              <div className="space-y-2">
                {['CONFIDENCIAL', 'SECRETO', 'TOP SECRET'].map((level) => (
                  <label key={level} className="flex items-center gap-2 text-sm text-slate-300">
                    <input type="radio" name="clearance" className="text-amber-600" />
                    {level}
                  </label>
                ))}
              </div>
            </div>

            <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
              <h3 className="text-sm font-semibold text-slate-100 mb-3 flex items-center gap-2">
                <Calendar size={14} />
                Distribución
              </h3>
              <div className="space-y-1 text-xs text-slate-400">
                <p>• Exportación para analistas</p>
                <p>• Envío cifrado (PGP/GPG)</p>
                <p>• Integración con SIEM</p>
                <p>• Archivo en base de datos</p>
              </div>
            </div>

            <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
              <h3 className="text-sm font-semibold text-slate-100 mb-3 flex items-center gap-2">
                <Mail size={14} />
                Destinatarios
              </h3>
              <div className="space-y-1 text-xs text-slate-400">
                <p>• Mando Superior</p>
                <p>• Unidad de Inteligencia</p>
                <p>• Fuerzas y Cuerpos de Seguridad</p>
                <p>• Autoridades Judiciales</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Plantillas */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-sm font-semibold text-slate-100 mb-4">Plantillas Disponibles</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { name: 'Ejecutivo', desc: 'Resumen para alta dirección' },
            { name: 'Técnico', desc: 'Análisis detallado para analistas' },
            { name: 'Legal', desc: 'Formato para autoridades judiciales' },
          ].map((template) => (
            <div key={template.name} className="bg-slate-900 p-4 rounded-lg border border-slate-700 cursor-pointer hover:border-amber-500 transition-colors">
              <h4 className="text-sm font-semibold text-slate-100">{template.name}</h4>
              <p className="text-xs text-slate-400 mt-1">{template.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
