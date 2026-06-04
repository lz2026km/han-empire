/* =============================================
   ConfirmDialog - 通用确认弹窗 (v5.2.0 P6-5 + v5.5.0+ P8-G6)
   4 种 variant: danger / warning / info / success
   ============================================= */
import { useEffect, useRef } from 'react'

type Variant = 'danger' | 'warning' | 'info' | 'success'

interface ConfirmDialogProps {
  open: boolean
  title: string
  body?: string
  confirmText?: string
  cancelText?: string
  variant?: Variant
  loading?: boolean
  onConfirm: () => void
  onCancel: () => void
}

const VARIANT_META: Record<Variant, { icon: string; color: string; bg: string; cls: string }> = {
  danger:  { icon: '/status/error_spring.jpg',   color: '#c42b2b', bg: 'rgba(196, 43, 43, 0.12)',  cls: 'status-badge--error' },
  warning: { icon: '/status/warning_spring.jpg', color: '#d4a017', bg: 'rgba(212, 160, 23, 0.12)', cls: 'status-badge--warning' },
  info:    { icon: '/status/info_spring.jpg',    color: '#5b8fb9', bg: 'rgba(91, 143, 185, 0.12)', cls: 'status-badge--info' },
  success: { icon: '/status/success_spring.jpg', color: '#5bbf6b', bg: 'rgba(91, 191, 107, 0.12)', cls: 'status-badge--success' },
}

export function ConfirmDialog({
  open, title, body, confirmText = '确认', cancelText = '取消',
  variant = 'warning', loading, onConfirm, onCancel,
}: ConfirmDialogProps) {
  const confirmRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel()
      else if (e.key === 'Enter' && !loading) onConfirm()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, loading, onConfirm, onCancel])

  useEffect(() => {
    if (open && confirmRef.current) confirmRef.current.focus()
  }, [open])

  if (!open) return null

  const meta = VARIANT_META[variant]

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal modal--confirm" onClick={e => e.stopPropagation()}
        style={{ maxWidth: '440px' }}>
        <div style={{
          display: 'flex', alignItems: 'flex-start', gap: '12px',
          padding: '4px 0 12px',
        }}>
          <div className={`status-badge ${meta.cls}`} style={{
            width: '36px', height: '36px', borderRadius: '50%',
            background: meta.bg, color: meta.color,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
            padding: 0,
          }}>
            <img className="status-badge__icon" src={meta.icon} alt=""
              style={{ width: '24px', height: '24px' }} />
          </div>
          <div style={{ flex: 1 }}>
            <div className="modal__title" style={{ marginBottom: '4px' }}>{title}</div>
            {body && (
              <p style={{
                color: 'var(--color-text-secondary)',
                fontSize: '13px', lineHeight: 1.6,
                margin: 0,
              }}>{body}</p>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '8px' }}>
          <button type="button" className="btn" onClick={onCancel} disabled={loading}>
            <img className="settings-section__icon" src="/btn/btn_cancel.jpg" alt=""
              style={{ width: '14px', height: '14px', marginRight: 4 }} />
            {cancelText}
          </button>
          <button
            ref={confirmRef}
            type="button"
            className={`btn ${variant === 'danger' ? 'btn--danger' : 'btn--primary'}`}
            onClick={onConfirm}
            disabled={loading}
            style={variant === 'danger' ? { background: meta.color, color: '#fff' } : undefined}
          >
            <img className="settings-section__icon" src="/btn/btn_confirm.jpg" alt=""
              style={{ width: '14px', height: '14px', marginRight: 4 }} />
            {loading ? '处理中...' : confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
