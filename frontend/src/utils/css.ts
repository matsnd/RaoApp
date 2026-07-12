/**
 * Helper do czytania zmiennych CSS z :root.
 * Używane przez useChartTheme do synchronizacji kolorów Chart.js z design system.
 */
export function getCssVar(name: string, fallback: string = ''): string {
  if (typeof window === 'undefined') return fallback
  const root = document.documentElement
  const value = getComputedStyle(root).getPropertyValue(name).trim()
  return value || fallback
}
