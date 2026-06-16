import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { AlertStatus, RiskLevel } from './types'

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

export const RISK_CARD_CLASSES: Record<RiskLevel, string> = {
  VERDE:    'border-green-500 bg-green-500/10',
  AMARILLO: 'border-yellow-500 bg-yellow-500/10',
  NARANJA:  'border-orange-500 bg-orange-500/10',
  ROJO:     'border-red-500 bg-red-500/10',
}

export const RISK_BADGE_CLASSES: Record<RiskLevel, string> = {
  VERDE:    'bg-green-500/20 text-green-400',
  AMARILLO: 'bg-yellow-500/20 text-yellow-400',
  NARANJA:  'bg-orange-500/20 text-orange-400',
  ROJO:     'bg-red-500/20 text-red-400',
}

export const RISK_LABELS: Record<RiskLevel, string> = {
  VERDE:    'Bajo',
  AMARILLO: 'Medio',
  NARANJA:  'Alto',
  ROJO:     'Crítico',
}

export const STATUS_TEXT_CLASSES: Record<AlertStatus, string> = {
  PENDIENTE:      'text-yellow-400',
  ESCALADA:       'text-red-400',
  ARCHIVADA:      'text-slate-400',
  FALSO_POSITIVO: 'text-green-400',
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
