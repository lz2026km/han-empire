// v2.0.0 Phase 3.1: 总览 Tab - 朝会视角（汉风重命名）
// 抽自 App.tsx:421-485 (65 行)
import type { GameState, MinisterStats } from '../../types'

interface OverviewTabProps {
  gameState: GameState | null
  ministers: MinisterStats[]
  factions: any[]
  onNextTurn: () => void
  onSave: () => void
}

function getAuthorityTier(authority: number): string {
  if (authority >= 90) return '九五之尊'
  if (authority >= 75) return '乾纲独断'
  if (authority >= 60) return '亲贤辅政'
  if (authority >= 45) return '垂拱而治'
  if (authority >= 30) return '受制于人'
  if (authority >= 15) return '寄人篱下'
  return '待宰羔羊'
}

export function OverviewTab({ gameState, ministers, factions, onNextTurn, onSave }: OverviewTabProps) {
  if (!gameState) return null
  return (
    <div className="fade-in">
      <div className="action-row">
        <button className="btn btn--primary" onClick={onNextTurn}>下️ 下一个月</button>
        {/* v2.0.0 P0-B1: 存档按钮接 saveGame */}
        <button className="btn btn--gold" onClick={onSave}>存储 存档</button>
      </div>

      <div className="grid-3" style={{ marginBottom: '20px' }}>
        <div className="card card--gold">
          <div style={{ color: 'var(--color-gold)', fontSize: '13px', marginBottom: '8px' }}>威权值</div>
          <div style={{ fontSize: '36px', color: 'var(--color-gold-bright)', marginBottom: '8px' }}>
            {gameState.emperor_authority}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
            七档: {getAuthorityTier(gameState.emperor_authority)}阶
          </div>
        </div>
        <div className="card">
          <div style={{ color: 'var(--color-text-secondary)', fontSize: '13px', marginBottom: '8px' }}>忠诚度</div>
          <div style={{ fontSize: '36px', color: 'var(--color-text-primary)' }}>
            {gameState.emperor_loyalty}
          </div>
        </div>
        <div className="card">
          <div style={{ color: 'var(--color-text-secondary)', fontSize: '13px', marginBottom: '8px' }}>在册大臣</div>
          <div style={{ fontSize: '36px', color: 'var(--color-text-primary)' }}>
            {ministers.length}
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div style={{ color: 'var(--color-gold)', marginBottom: '12px' }}>派系形势</div>
          {factions.map(f => (
            <div key={f.id} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span>{f.name}</span>
              <span style={{ color: 'var(--color-gold)' }}>{f.influence}</span>
            </div>
          ))}
        </div>
        <div className="card">
          <div style={{ color: 'var(--color-gold)', marginBottom: '12px' }}>近期大臣</div>
          {ministers.slice(0, 5).map(m => (
            <div key={m.id} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span>{m.name}</span>
              <span style={{ color: 'var(--color-text-muted)' }}>{m.faction}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}