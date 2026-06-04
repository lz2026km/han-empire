/* =============================================
   ReportModal - 月初邸报弹窗 (v5.1.1 P1-3)
   v5.1 内部设计 ReportModal, 全屏竹简底图 + 文言风叙事
   ============================================= */
import { useEffect, useRef, useState } from 'react'
import { X, Copy, Check, ScrollText } from 'lucide-react'

interface Gazette {
  turn: number
  year: number
  period: number
  report: string
  created_at?: string
}

interface ReportModalProps {
  open: boolean
  gazette: Gazette | null
  onClose: () => void
}

export function ReportModal({ open, gazette, onClose }: ReportModalProps) {
  const [copied, setCopied] = useState(false)
  const bodyRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open || !gazette) return null

  const copyText = async () => {
    try {
      await navigator.clipboard.writeText(gazette.report || '')
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="report-modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="月初邸报">
      <div className="report-modal" onClick={(e) => e.stopPropagation()}>
        <div className="report-modal__titlebar">
          <div className="report-modal__title">
            <ScrollText size={18} />
            <span>{gazette.year}年{gazette.period}月 · 月末邸报 · 回合 {gazette.turn}</span>
          </div>
          <div className="report-modal__actions">
            <button type="button" className="report-modal__btn" onClick={copyText} aria-label="复制邸报">
              {copied ? <Check size={16} /> : <Copy size={16} />}
              <span>{copied ? '已复制' : '复制'}</span>
            </button>
            <button type="button" className="report-modal__btn report-modal__btn--close" onClick={onClose} aria-label="关闭">
              <X size={16} />
              <span>朕已知悉</span>
            </button>
          </div>
        </div>
        <div className="report-modal__body" ref={bodyRef}>
          <pre className="report-modal__text">{gazette.report || '（无内容）'}</pre>
        </div>
        <div className="report-modal__footer">
          <span>创建: {gazette.created_at || '未知'}</span>
        </div>
      </div>
    </div>
  )
}
