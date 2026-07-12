/**
 * Centralny theme Chart.js zsynchronizowany z CSS variables RAO.
 * Tree-shake: rejestrujemy tylko potrzebne komponenty.
 */
import {
  Chart,
  BarController,
  LineController,
  DoughnutController,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  Filler,
  type ChartOptions,
} from 'chart.js'
import { getCssVar } from '@/utils/css'

Chart.register(
  BarController,
  LineController,
  DoughnutController,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  Filler,
)

export interface ChartColors {
  primary: string
  primaryLight: string
  info: string
  success: string
  warning: string
  error: string
  border: string
  textMuted: string
  bgLight: string
  fontFamily: string
}

export function useChartTheme() {
  const colors: ChartColors = {
    primary: getCssVar('--color-primary', '#1D2B53'),
    primaryLight: getCssVar('--color-primary-light', '#2A3F6F'),
    info: getCssVar('--color-info', '#3B82F6'),
    success: getCssVar('--color-success', '#22C55E'),
    warning: getCssVar('--color-warning', '#F59E0B'),
    error: getCssVar('--color-error', '#EF4444'),
    border: getCssVar('--color-border', '#E2E8F0'),
    textMuted: getCssVar('--color-text-muted', '#718096'),
    bgLight: getCssVar('--color-bg-light', '#F8F9FA'),
    fontFamily: getCssVar('--font-family', 'Montserrat, sans-serif'),
  }

  const baseOptions: ChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: colors.primary,
        titleColor: '#FFFFFF',
        bodyColor: '#FFFFFF',
        titleFont: { family: colors.fontFamily, weight: 600 as const, size: 13 },
        bodyFont: { family: colors.fontFamily, size: 12 },
        padding: 12,
        cornerRadius: 8,
        displayColors: false,
      },
    },
    scales: {
      x: {
        grid: { color: colors.border },
        ticks: { color: colors.textMuted, font: { family: colors.fontFamily, size: 11 } },
        border: { color: colors.border },
      },
      y: {
        grid: { color: colors.border },
        ticks: { color: colors.textMuted, font: { family: colors.fontFamily, size: 11 } },
        border: { color: colors.border },
      },
    },
  }

  return { colors, baseOptions }
}
