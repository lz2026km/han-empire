import { useState, useEffect, useCallback } from 'react'
import './Notification.css'

export type NotificationType = 'info' | 'success' | 'warning' | 'critical' | 'decree' | 'battle' | 'political'

export interface NotificationItem {
  id: string
  type: NotificationType
  title: string
  message: string
  timestamp: number
  duration?: number
  important?: boolean
}

const TYPE_ICONS: Record<NotificationType, string> = {
  info: '列表', success: '[OK]', warning: '[警告]️', critical: '警',
  decree: '诏书', battle: '战斗️', political: '建筑️',
}

const TYPE_COLORS: Record<NotificationType, string> = {
  info: 'var(--color-text-secondary)', success: '#22c55e', warning: '#f59e0b',
  critical: 'var(--color-accent-red-bright)', decree: 'var(--color-gold)',
  battle: 'var(--color-accent-red)', political: 'var(--color-gold-dim)',
}

export function NotificationCenter({ notifications, onDismiss }: { notifications: NotificationItem[]; onDismiss: (id: string) => void }) {
  return (
    <div className="notification-center" aria-live="polite">
      {notifications.map((n, i) => (
        <NotificationToast key={n.id} notification={n} onDismiss={onDismiss} style={{ animationDelay: `${i * 0.1}s` }} />
      ))}
    </div>
  )
}

function NotificationToast({ notification, onDismiss, style }: { notification: NotificationItem; onDismiss: (id: string) => void; style?: React.CSSProperties }) {
  const [isExiting, setIsExiting] = useState(false)
  const typeColor = TYPE_COLORS[notification.type]

  useEffect(() => {
    const dur = notification.duration ?? 4000
    if (dur > 0) {
      const t = setTimeout(() => { setIsExiting(true); setTimeout(() => onDismiss(notification.id), 300) }, dur)
      return () => clearTimeout(t)
    }
  }, [notification.duration, notification.id, onDismiss])

  return (
    <div
      className={`notification-toast ${isExiting ? 'toast-exit' : 'toast-enter'} ${notification.important ? 'notification-toast--important' : ''}`}
      style={{ borderLeftColor: typeColor, ...style }}
      role="alert"
    >
      <div className="notification-toast__icon" style={{ color: typeColor }}>{TYPE_ICONS[notification.type]}</div>
      <div className="notification-toast__content">
        <div className="notification-toast__title" style={{ color: typeColor }}>{notification.title}</div>
        <div className="notification-toast__message">{notification.message}</div>
      </div>
      <button type="button" className="notification-toast__close" onClick={() => { setIsExiting(true); setTimeout(() => onDismiss(notification.id), 300) }}>×</button>
    </div>
  )
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([])

  const add = useCallback((type: NotificationType, title: string, message: string, opts?: { duration?: number; important?: boolean }) => {
    const id = `notif-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    setNotifications(prev => [{ id, type, title, message, timestamp: Date.now(), duration: opts?.duration ?? 4000, important: opts?.important ?? false }, ...prev].slice(0, 10))
    return id
  }, [])

  const dismiss = useCallback((id: string) => setNotifications(prev => prev.filter(n => n.id !== id)), [])
  const clear = useCallback(() => setNotifications([]), [])

  return { notifications, addNotification: add, dismissNotification: dismiss, clearAll: clear }
}