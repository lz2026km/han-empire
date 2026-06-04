// v2.0.0 Phase 3.1: 抽自 App.tsx:541-626 (86 行)
// 汉风术语："朝堂"对应 courtMode 视图，"在朝"指官员在朝任职状态
import { useState, useMemo } from 'react'  // v2.0.0 Phase 5.6: 加 useMemo
import type { MinisterStats } from '../../types'
import { CourtLayout } from '../CourtLayout'
import { MinisterPortrait } from '../MinisterPortrait'

interface MinisterTabProps {
  ministers: MinisterStats[]
}

export function MinisterTab({ ministers }: MinisterTabProps) {
  const [courtMode, setCourtMode] = useState<'grid' | 'court'>('grid')

  const handleMinisterClick = (m: MinisterStats) => {
    // TODO: Open chat with minister
    console.log('Selected minister:', m.name)
  }

  // v2.0.0 Phase 5.6: 缓存 courtMinisters 转换, 避免每次 render 重算
  const courtMinisters = useMemo(() => ministers.map(m => ({
    id: String(m.id),
    name: m.name,
    office: m.position,
    faction: m.faction,
    status: 'active' as const,
    status_label: '在朝',
    summary: `忠诚${m.loyalty} | 能力${m.ability}`,
    portrait_id: m.portrait,
  })), [ministers])

  return (
    <div className="fade-in">
      <div className="minister-tab-header">
        <div className="minister-tab-tabs">
          <button
            className={`minister-tab-btn ${courtMode === 'grid' ? 'active' : ''}`}
            onClick={() => setCourtMode('grid')}
          >
            网格视图
          </button>
          <button
            className={`minister-tab-btn ${courtMode === 'court' ? 'active' : ''}`}
            onClick={() => setCourtMode('court')}
          >
            朝会视图
          </button>
        </div>
      </div>

      {courtMode === 'grid' ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '12px' }}>
          {ministers.map(m => (
            <div key={m.id} className="minister-card">
              <div className="minister-card-portrait-wrap">
                <MinisterPortrait
                  primary={m.portrait ? `/portraits/minister_${m.id}.png` : undefined}
                  name={m.name}
                  size="medium"
                />
              </div>
              <div className="minister-card__info">
                <div className="minister-card__name">{m.name}</div>
                <div className="minister-card__stats">
                  <span>{m.position}</span>
                  <span className="minister-card__faction" style={{ background: `var(--faction-${m.faction})` }}>
                    {m.faction}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '12px', marginTop: '6px' }}>
                  <div className="minister-stat-bar">
                    <span className="minister-stat-bar__label">忠</span>
                    <div className="minister-stat-bar__track">
                      <div className="minister-stat-bar__fill" style={{ width: `${m.loyalty}%`, background: 'var(--color-gold)' }} />
                    </div>
                  </div>
                  <div className="minister-stat-bar">
                    <span className="minister-stat-bar__label">能</span>
                    <div className="minister-stat-bar__track">
                      <div className="minister-stat-bar__fill" style={{ width: `${m.ability}%`, background: 'var(--color-accent-red)' }} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <CourtLayout
          ministers={courtMinisters}
          selectedMinister=""
          onOpenChat={handleMinisterClick as any}
          courtMode="grid"
        />
      )}
    </div>
  )
}