/* =============================================
   HistoryModal - 回合历史弹窗 (v5.1.2 P2-2)
   仿 ming_sim HistoryModal, 3 Tab: Summary / Decisions / Closed
   ============================================= */
import { useEffect, useRef, useState } from 'react'
import { X, History, ScrollText, ListChecks, ScrollText as Scroll } from 'lucide-react'

type Tab = 'summary' | 'decisions' | 'closed'

interface Summary {
  turn: number
  year: number
  period: number
  report: string
  created_at?: string
}

interface Decision {
  turn: number
  decision_type?: string
  action?: string
  description?: string
  timestamp?: string
}

interface ClosedIssue {
  turn: number
  id: number
  title: string
  status: 'resolved' | 'failed' | 'dropped'
  kind?: string
  effect_on_resolve?: Record<string, number>
}

interface HistoryData {
  campaign_id: string
  current_turn?: number
  summaries?: Summary[]
  decisions?: Decision[]
  closed_issues?: ClosedIssue[]
}

interface HistoryModalProps {
  open: boolean
  data: HistoryData | null
  onClose: () => void
}

export function HistoryModal({ open, data, onClose }: HistoryModalProps) {
  const [tab, setTab] = useState<Tab>('summary')
  const bodyRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = 0
  }, [tab, open])

  if (!open || !data) return null

  const summaries = data.summaries || []
  const decisions = data.decisions || []
  const closed = data.closed_issues || []

  const renderSummary = (s: Summary) => (
    <li key={`s-${s.turn}`} className="hist-item">
      <div className="hist-item__head">
        <span className="hist-item__id">T{s.turn}</span>
        <span className="hist-item__date">{s.year}年{s.period}月</span>
        <span className="hist-item__count">{s.report?.length || 0} 字</span>
      </div>
      <pre className="hist-item__text">{s.report || '（无内容）'}</pre>
    </li>
  )

  const renderDecision = (d: Decision, idx: number) => (
    <li key={`d-${d.turn}-${idx}`} className="hist-item">
      <div className="hist-item__head">
        <span className="hist-item__id">T{d.turn}</span>
        <span className="hist-item__type">{d.decision_type || '诏书'}</span>
        <span className="hist-item__action">{d.action || '-'}</span>
      </div>
      {d.description ? <div className="hist-item__desc">{d.description}</div> : null}
      {d.timestamp ? (
        <div className="hist-item__time">{d.timestamp}</div>
      ) : null}
    </li>
  )

  const renderClosed = (c: ClosedIssue, idx: number) => {
    const statusCls =
      c.status === 'failed' ? 'hist-badge--failed' :
      c.status === 'dropped' ? 'hist-badge--dropped' :
      'hist-badge--resolved'
    return (
      <li key={`c-${c.turn}-${idx}`} className="hist-item">
        <div className="hist-item__head">
          <span className="hist-item__id">T{c.turn}</span>
          <span className="hist-item__id">#{c.id}</span>
          <span className={`hist-badge ${statusCls}`}>
            {c.status === 'resolved' ? '已了' : c.status === 'failed' ? '崩坏' : '撤销'}
          </span>
          <span className="hist-item__action">{c.title || '-'}</span>
        </div>
        {c.effect_on_resolve && Object.keys(c.effect_on_resolve).length > 0 ? (
          <div className="hist-effects">
            {Object.entries(c.effect_on_resolve).map(([k, v]) => (
              <span key={k} className={v >= 0 ? 'hist-pos' : 'hist-neg'}>
                {k} {v > 0 ? `+${v}` : v}
              </span>
            ))}
          </div>
        ) : null}
      </li>
    )
  }

  return (
    <div className="hist-modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="回合历史">
      <div className="hist-modal" onClick={(e) => e.stopPropagation()}>
        <div className="hist-modal__titlebar">
          <div className="hist-modal__title">
            <History size={18} />
            <span>回合历史 · T{data.current_turn ?? '?'}</span>
          </div>
          <button type="button" className="hist-modal__close" onClick={onClose} aria-label="关闭">
            <X size={16} />
            <span>关闭</span>
          </button>
        </div>
        <div className="hist-modal__tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'summary'}
            className={`hist-tab ${tab === 'summary' ? 'hist-tab--active' : ''}`}
            onClick={() => setTab('summary')}
          >
            <ScrollText size={14} /> 邸报 ({summaries.length})
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'decisions'}
            className={`hist-tab ${tab === 'decisions' ? 'hist-tab--active' : ''}`}
            onClick={() => setTab('decisions')}
          >
            <Scroll size={14} /> 决策 ({decisions.length})
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'closed'}
            className={`hist-tab ${tab === 'closed' ? 'hist-tab--active' : ''}`}
            onClick={() => setTab('closed')}
          >
            <ListChecks size={14} /> 关案 ({closed.length})
          </button>
        </div>
        <div className="hist-modal__body" ref={bodyRef}>
          {tab === 'summary' && (
            summaries.length === 0 ? (
              <div className="hist-empty">暂无邸报记录</div>
            ) : (
              <ul className="hist-list">{summaries.map(renderSummary)}</ul>
            )
          )}
          {tab === 'decisions' && (
            decisions.length === 0 ? (
              <div className="hist-empty">暂无决策记录</div>
            ) : (
              <ul className="hist-list">{decisions.map(renderDecision)}</ul>
            )
          )}
          {tab === 'closed' && (
            closed.length === 0 ? (
              <div className="hist-empty">暂无结案记录</div>
            ) : (
              <ul className="hist-list">{closed.map(renderClosed)}</ul>
            )
          )}
        </div>
      </div>
    </div>
  )
}
