// v2.0.0 Phase 3.1: 抽自 App.tsx:628-689 (62 行)
// 汉风术语："派系"对应 factions (汉末群雄割据：董、曹、袁等)
import { useState } from 'react'
import type { FactionStats } from '../../types'
import { FactionRelationDiagram } from '../FactionRelationDiagram'

interface FactionTabProps {
  factions: FactionStats[]
}

export function FactionTab({ factions }: FactionTabProps) {
  const [showDiagram, setShowDiagram] = useState(false)

  const factionNodes = factions.map(f => ({
    id: f.id,
    name: f.name,
    influence: f.influence,
    color: f.color || 'var(--color-gold)',
    ministers: [],
    description: f.description || `${f.name} - 影响力: ${f.influence}`,
  }))

  // mockRelations: 东/曹/袁/汉 的对抗与联盟关系（汉末三国雏形）
  const mockRelations = [
    { source: 'dong', target: 'cao', type: 'rival' as const, strength: 80 },
    { source: 'yuan', target: 'cao', type: 'rival' as const, strength: 60 },
    { source: 'han', target: 'dong', type: 'alliance' as const, strength: 70 },
    { source: 'han', target: 'cao', type: 'rival' as const, strength: 90 },
  ]

  return (
    <div className="fade-in">
      <div className="faction-tab-header">
        <button type="button"
          className={`faction-view-btn ${showDiagram ? 'active' : ''}`}
          onClick={() => setShowDiagram(!showDiagram)}
        >
          {showDiagram ? '返回列表' : '派系关系图'}
        </button>
      </div>

      {showDiagram ? (
        <div className="faction-diagram-container">
          <FactionRelationDiagram
            factions={factionNodes}
            relations={mockRelations}
            width={700}
            height={450}
          />
        </div>
      ) : (
        <div className="faction-panel">
          {factions.map(f => (
            <div key={f.id} className="faction-card">
              <div className="faction-card__header">
                <span className="faction-card__name" style={{ color: f.color || 'var(--color-gold)' }}>
                  {f.name}
                </span>
                <span className="faction-card__influence">{f.influence}</span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                首领: {f.leader_name}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                影响力 {f.influence}，{f.dominant_ministers}名大臣
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
