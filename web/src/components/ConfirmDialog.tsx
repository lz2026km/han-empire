/* =============================================
   ConfirmDialog - 通用确认弹窗 (v5.2.0 P6-5)
   仿 ming_sim ConfirmDialog, 4 种 variant
   ============================================= */
import { useEffect, useRef } from 'react'
import { AlertTriangle, Info, AlertCircle, CheckCircle2 } from 'lucide-react'

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

const VARIANT_META: Record<Variant, { icon: any; color: string; bg: string }> = {
  danger: { icon: AlertTriangle, color: '#c42b2b', bg: 'rgba(196, 43, 43, 0.12)' },
  warning: { icon: AlertCircle, color: '#d4a017', bg: 'rgba(212, 160, 23, 0.12)' },
  info: { icon: Info, color: '#5b8fb9', bg: 'rgba(91, 143, 185, 0.12)' },
  success: { icon: CheckCircle2, color: '#5bbf6b', bg: 'rgba(91, 191, 107, 0.12)' },
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
  const Icon = meta.icon

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal modal--confirm" onClick={e => e.stopPropagation()}
        style={{ maxWidth: '440px' }}>
        <div style={{
          display: 'flex', alignItems: 'flex-start', gap: '12px',
          padding: '4px 0 12px',
        }}>
          <div style={{
            width: '36px', height: '36px', borderRadius: '50%',
            background: meta.bg, color: meta.color,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <Icon size={20} />
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
            {loading ? '处理中...' : confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
