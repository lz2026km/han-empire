// v2.1.0 Phase 3.1: 全局快捷键 hook
// 用法: useKeyboard({ '1': () => switchTab(0), '2': () => switchTab(1), ... })
import { useEffect } from 'react'

export type ShortcutMap = Record<string, (e: KeyboardEvent) => void>

export function useKeyboard(shortcuts: ShortcutMap, enabled = true) {
  useEffect(() => {
    if (!enabled) return
    const handler = (e: KeyboardEvent) => {
      // 忽略输入框
      const target = e.target as HTMLElement
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) {
        return
      }
      const key = e.key.toLowerCase()
      const action = shortcuts[key] || shortcuts[e.key]
      if (action) {
        e.preventDefault()
        action(e)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [shortcuts, enabled])
}
