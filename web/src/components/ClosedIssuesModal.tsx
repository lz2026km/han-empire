/* =============================================
   ClosedIssuesModal - 关案弹窗 (v5.1.2 P2-1)
   v5.1 内部设计 ClosedIssuesModal, 月末自动弹
   ============================================= */
import { useEffect, useRef } from 'react'
import { X, Check, ListChecks } from 'lucide-react'

interface ClosedIssue {
  id: number
  kind?: string
  title: string
  status: 'resolved' | 'failed' | 'dropped'
  bar_value?: number
  bar_good_meaning?: string
  bar_bad_meaning?: string
  closed_turn?: number
  stage_text?: string
  effect_on_resolve?: Record<string, number>
  tags?: string[]
}

interface ClosedIssuesModalProps {
  open: boolean
  issues: ClosedIssue[]
  onClose: () => void
}

const STATUS_BADGE: Record<string, { label: string; cls: string }> = {
  resolved: { label: '已了', cls: 'closed-badge--resolved' },
  failed: { label: '崩坏', cls: 'closed-badge--failed' },
  dropped: { label: '撤销', cls: 'closed-badge--dropped' },
}

export function ClosedIssuesModal({ open, issues, onClose }: ClosedIssuesModalProps) {
  const bodyRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  const renderEffect = (eff?: Record<string, number>) => {
    if (!eff || Object.keys(eff).length === 0) return <span className="closed-muted">无直接数值影响</span>
    return (
      <ul className="closed-effects">
        {Object.entries(eff).map(([k, v]) => (
          <li key={k}>
            <b>{k}</b>
            <span className={v >= 0 ? 'closed-pos' : 'closed-neg'}>
              {v > 0 ? `+${v}` : v}
            </span>
          </li>
        ))}
      </ul>
    )
  }

  return (
    <div className="closed-modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="事项关案">
      <div className="closed-modal" onClick={(e) => e.stopPropagation()}>
        <div className="closed-modal__titlebar">
          <div className="closed-modal__title">
            <img
              src="/portraits/main/liuxie_emperor.jpg"
              alt="主公"
              style={{ width: 28, height: 28, borderRadius: '50%', objectFit: 'cover', border: '1px solid var(--color-gold-dim)' }}
              onError={(e) => { e.currentTarget.style.display = 'none' }}
            />
            <span>本月关案 · {issues.length} 项</span>
          </div>
          <button type="button" className="closed-modal__close" onClick={onClose} aria-label="关闭">
            <X size={16} />
            <span>朕已知悉</span>
          </button>
        </div>
        <div className="closed-modal__body" ref={bodyRef}>
          {issues.length === 0 ? (
            <div className="closed-empty">本月无事项关案</div>
          ) : (
            <ul className="closed-list">
              {issues.map((it) => {
                const badge = STATUS_BADGE[it.status] || STATUS_BADGE.resolved
                return (
                  <li key={it.id} className="closed-item">
                    <div className="closed-item__head">
                      <span className="closed-item__id">#{it.id}</span>
                      <span className={`closed-badge ${badge.cls}`}>
                        <Check size={12} /> {badge.label}
                      </span>
                      <span className="closed-item__title">{it.title || '未命名'}</span>
                      {it.closed_turn ? (
                        <span className="closed-item__turn">T{it.closed_turn}</span>
                      ) : null}
                    </div>
                    {it.stage_text ? (
                      <div className="closed-item__stage">{it.stage_text}</div>
                    ) : null}
                    <div className="closed-item__bar">
                      <span className="closed-item__bar-label">进度</span>
                      <div className="closed-item__bar-track">
                        <div
                          className="closed-item__bar-fill"
                          style={{ width: `${Math.max(0, Math.min(100, it.bar_value ?? 0))}%` }}
                        />
                      </div>
                      <span className="closed-item__bar-value">
                        {it.bar_value ?? 0} / 100
                      </span>
                    </div>
                    {renderEffect(it.effect_on_resolve)}
                    {it.tags && it.tags.length > 0 ? (
                      <div className="closed-tags">
                        {it.tags.map((t) => (
                          <span key={t} className="closed-tag">{t}</span>
                        ))}
                      </div>
                    ) : null}
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
