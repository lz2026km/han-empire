/* =============================================
   StateModal - 国势详情弹窗 (v5.1.4 P4-3)
   v5.1 内部设计 StateModal, 6 Tab: 国势/财政/派系/地区/军队/外部
   ============================================= */
import { useEffect, useRef, useState } from 'react'
import { X, BarChart3, Coins, Users, Map, Sword, Globe } from 'lucide-react'

interface BudgetAccount {
  balance: number
  income: any[]
  expense: any[]
  income_total: number
  expense_total: number
  net: number
}

interface StateModalProps {
  open: boolean
  gameState: any
  // v5.2.0 P6-2: budget 改为可选 (不传则从 gameState.metrics["汉室库"/"内库"] 读)
  budget?: { 汉室库: BudgetAccount; 内库: BudgetAccount } | null
  factions?: any[]
  regions?: any[]
  armies?: any[]
  onClose: () => void
}

type Tab = 'state' | 'budget' | 'factions' | 'regions' | 'armies' | 'world'

const TAB_LABEL: Record<Tab, { label: string; icon: any }> = {
  state: { label: '国势', icon: BarChart3 },
  budget: { label: '财政', icon: Coins },
  factions: { label: '派系', icon: Users },
  regions: { label: '地区', icon: Map },
  armies: { label: '军队', icon: Sword },
  world: { label: '外部', icon: Globe },
}

function formatMoney(n: number) {
  return `${n} 万两`
}

export function StateModal({ open, gameState, budget, factions, regions, armies, onClose }: StateModalProps) {
  const [tab, setTab] = useState<Tab>('state')
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

  if (!open || !gameState) return null

  const renderState = () => {
    const metrics = gameState.metrics || {}
    const entries = Object.entries(metrics)
    return (
      <div className="state-grid">
        {entries.map(([k, v]) => (
          <div key={k} className="state-metric">
            <div className="state-metric__label">{k}</div>
            <div className="state-metric__value">{String(v)}</div>
          </div>
        ))}
      </div>
    )
  }

  const renderBudget = () => {
    // v5.2.0 P6-2: 优先用 budget prop, 否则从 gameState.metrics 合成 (单数字 fallback)
    const effBudget = budget || (gameState?.metrics ? {
      汉室库: {
        balance: Number(gameState.metrics['汉室库'] || 0),
        net: 0, income_total: 0, expense_total: 0,
        income: [], expense: [],
      },
      内库: {
        balance: Number(gameState.metrics['内库'] || 0),
        net: 0, income_total: 0, expense_total: 0,
        income: [], expense: [],
      },
    } : null)
    if (!effBudget) return <div className="state-empty">财政数据加载中...</div>
    const renderAccount = (label: string, acc: BudgetAccount | undefined) => {
      if (!acc) return null
      const detail = acc.income_total || acc.expense_total
      return (
        <div className="state-account">
          <h4>{label}</h4>
          <div className="state-account__balance">{formatMoney(acc.balance)}</div>
          {detail ? (
            <div className="state-account__net" style={{ color: acc.net >= 0 ? '#4ade80' : '#f87171' }}>
              月净: {acc.net > 0 ? '+' : ''}{formatMoney(acc.net)}
            </div>
          ) : (
            <div className="state-account__net" style={{ color: 'var(--color-text-muted)' }}>
              (详细流水需 1 个回合后生成)
            </div>
          )}
          {detail ? (
            <div className="state-account__detail">
              <div className="state-account__income">
                <strong>收入 ({acc.income_total})</strong>
                <ul>
                  {acc.income.map((it, i) => (
                    <li key={i}>
                      {it.name}: {formatMoney(it.amount)}
                      {it.note && <span className="state-account__note"> - {it.note}</span>}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="state-account__expense">
                <strong>支出 ({acc.expense_total})</strong>
                <ul>
                  {acc.expense.map((it, i) => (
                    <li key={i}>
                      {it.name}: {formatMoney(it.amount)}
                      {it.note && <span className="state-account__note"> - {it.note}</span>}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : null}
        </div>
      )
    }
    return (
      <div className="state-budget">
        {renderAccount('汉室库 (公帑)', effBudget.汉室库)}
        {renderAccount('内库 (私帑)', effBudget.内库)}
      </div>
    )
  }

  const renderFactions = () => {
    const list = factions || []
    if (list.length === 0) return <div className="state-empty">暂无派系数据</div>
    return (
      <ul className="state-list">
        {list.map((f, i) => (
          <li key={i} className="state-list__item">
            <div className="state-list__head">
              <b>{f.name || '派系'}</b>
              <span>满意度 {f.satisfaction ?? '—'}</span>
            </div>
            {f.agenda && <div className="state-list__agenda">{f.agenda}</div>}
          </li>
        ))}
      </ul>
    )
  }

  const renderRegions = () => {
    const list = regions || []
    if (list.length === 0) return <div className="state-empty">暂无地区数据</div>
    return (
      <ul className="state-list">
        {list.map((r, i) => (
          <li key={i} className="state-list__item">
            <div className="state-list__head">
              <b>{r.name || '州郡'}</b>
              <span>人口 {r.population ?? '—'}</span>
            </div>
            <div className="state-list__meta">
              民心 {r.public_support ?? '—'} · 动乱 {r.unrest ?? '—'} · 控制者 {r.controlled_by || '—'}
            </div>
          </li>
        ))}
      </ul>
    )
  }

  const renderArmies = () => {
    const list = armies || []
    if (list.length === 0) return <div className="state-empty">暂无军队数据</div>
    return (
      <ul className="state-list">
        {list.map((a, i) => (
          <li key={i} className="state-list__item">
            <div className="state-list__head">
              <b>{a.name || '军'}</b>
              <span>{a.manpower ?? '—'} 人</span>
            </div>
            <div className="state-list__meta">
              统帅 {a.commander || '—'} · 兵种 {a.troop_type || '—'} · 维护 {a.maintenance_per_turn ?? 0} 万两/月
            </div>
          </li>
        ))}
      </ul>
    )
  }

  const renderWorld = () => {
    const powers = gameState.powers || gameState.external_powers || []
    if (powers.length === 0) return <div className="state-empty">暂无外部势力数据</div>
    return (
      <ul className="state-list">
        {powers.map((p: any, i: number) => (
          <li key={i} className="state-list__item">
            <div className="state-list__head">
              <b>{p.name || '势力'}</b>
              <span>实力 {p.military_strength ?? p.leverage ?? '—'}</span>
            </div>
            <div className="state-list__meta">
              立场 {p.stance || '—'} · 满意度 {p.satisfaction ?? '—'} · {p.agenda || ''}
            </div>
          </li>
        ))}
      </ul>
    )
  }

  return (
    <div className="state-modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="国势详情">
      <div className="state-modal" onClick={(e) => e.stopPropagation()}>
        <div className="state-modal__titlebar">
          <div className="state-modal__title">
            <img
              src="/portraits/main/liuxie_emperor.jpg"
              alt="主公"
              style={{ width: 28, height: 28, borderRadius: '50%', objectFit: 'cover', border: '1px solid var(--color-gold-dim)' }}
              onError={(e) => { e.currentTarget.style.display = 'none' }}
            />
            <span>国势详情 · {gameState.turn?.year || '?'}年{gameState.turn?.period || '?'}月</span>
          </div>
          <button type="button" className="state-modal__close" onClick={onClose} aria-label="关闭">
            <X size={16} />
            <span>关闭</span>
          </button>
        </div>
        <div className="state-modal__tabs" role="tablist">
          {(Object.keys(TAB_LABEL) as Tab[]).map((t) => {
            const Icon = TAB_LABEL[t].icon
            return (
              <button
                key={t}
                type="button"
                role="tab"
                aria-selected={tab === t}
                className={`state-tab ${tab === t ? 'state-tab--active' : ''}`}
                onClick={() => setTab(t)}
              >
                <Icon size={14} /> {TAB_LABEL[t].label}
              </button>
            )
          })}
        </div>
        <div className="state-modal__body" ref={bodyRef}>
          {tab === 'state' && renderState()}
          {tab === 'budget' && renderBudget()}
          {tab === 'factions' && renderFactions()}
          {tab === 'regions' && renderRegions()}
          {tab === 'armies' && renderArmies()}
          {tab === 'world' && renderWorld()}
        </div>
      </div>
    </div>
  )
}
