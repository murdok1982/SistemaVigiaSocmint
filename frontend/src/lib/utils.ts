import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { RiskLevel } from './types'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const RISK_COLORS: Record<RiskLevel, string> = {
  VERDE:    '#22c55e',
  AMARILLO: '#eab308',
  NARANJA:  '#f97316',
  ROJO:     '#ef4444',
}

export const RISK_BG_CLASSES: Record<RiskLevel, string> = {
  VERDE:    'bg-green-500/10 text-green-400 border-green-500/30',
  AMARILLO: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  NARANJA:  'bg-orange-500/10 text-orange-400 border-orange-500/30',
  ROJO:     'bg-red-500/10 text-red-400 border-red-500/30',
}

export const RISK_LABELS: Record<RiskLevel, string> = {
  VERDE:    'Bajo',
  AMARILLO: 'Medio',
  NARANJA:  'Alto',
  ROJO:     'Crítico',
}

export function formatTimestamp(iso: string): string {
  return new Intl.DateTimeFormat('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
}

export function riskScorePercent(score: number): number {
  return Math.min(100, Math.max(0, Math.round(score * 100)))
}
