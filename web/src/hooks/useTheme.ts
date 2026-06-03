// v2.1.0 Phase 3.1: 主题 hook (暗/亮 + 季节)
import { useEffect, useState } from 'react'

export type Theme = 'light' | 'dark'
export type Season = 'spring' | 'summer' | 'autumn' | 'winter'

const STORAGE_KEY = 'han-empire-theme'

function getInitial(): { theme: Theme; season: Season } {
  if (typeof window === 'undefined') return { theme: 'light', season: 'spring' }
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      return { theme: parsed.theme || 'light', season: parsed.season || 'spring' }
    }
  } catch {}
  return { theme: 'light', season: 'spring' }
}

export function useTheme() {
  const [{ theme, season }, setState] = useState(getInitial)

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') root.classList.add('theme-dark')
    else root.classList.remove('theme-dark')
    document.body.setAttribute('data-season', season)
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ theme, season }))
    } catch {}
  }, [theme, season])

  return {
    theme,
    season,
    setTheme: (t: Theme) => setState(s => ({ ...s, theme: t })),
    setSeason: (s: Season) => setState(st => ({ ...st, season: s })),
    toggleTheme: () => setState(s => ({ ...s, theme: s.theme === 'dark' ? 'light' : 'dark' })),
    cycleSeason: () => {
      const order: Season[] = ['spring', 'summer', 'autumn', 'winter']
      setState(s => ({ ...s, season: order[(order.indexOf(s.season) + 1) % 4] }))
    }
  }
}
