// v2.0.0 Phase 3.1: 诏书 Tab - 抽自 App.tsx:487-539 (53 行)
import type { GameState, MinisterStats } from '../../types'

interface DecreeTabProps {
  gameState: GameState | null
  ministers: MinisterStats[]
  onIssue: (decreeType: string, targetId?: number) => void
}

export function DecreeTab({ gameState, ministers, onIssue }: DecreeTabProps) {
  const decreeTypes = gameState?.available_decree_types || []
  return (
    <div className="fade-in">
      <div style={{ marginBottom: '16px', color: 'var(--color-text-secondary)', fontSize: '13px' }}>
        选择诏书类型发布诏令，每种诏书有不同效果和威权消耗。
      </div>
      <div className="decree-grid">
        {decreeTypes.map(dt => (
          <DecreeCard key={dt} decreeType={dt} ministers={ministers} onIssue={onIssue} />
        ))}
      </div>
    </div>
  )
}

function DecreeCard({
  decreeType, onIssue
}: {
  decreeType: string
  ministers: MinisterStats[]
  onIssue: (decreeType: string, targetId?: number) => void
}) {
  const decreeMeta: Record<string, { name: string; effect: string; cost: number }> = {
    appoint: { name: '任命诏书', effect: '任命大臣，提升忠诚', cost: 5 },
    dismiss: { name: '贬谪诏书', effect: '贬谪大臣，降低其威权', cost: 8 },
    inspect: { name: '巡视州郡', effect: '提升威权，降低派系影响', cost: 3 },
    recruit: { name: '招贤纳士', effect: '随机获得大臣', cost: 10 },
    edict: { name: '颁布政令', effect: '提升威权，降低忠诚', cost: 6 },
    grant: { name: '封赏功臣', effect: '提升大臣忠诚，降低威权', cost: 7 },
  }
  const meta = decreeMeta[decreeType] || { name: decreeType, effect: '', cost: 5 }
  return (
    <div className="decree-card">
      <div className="decree-card__name">{meta.name}</div>
      <div className="decree-card__effect">{meta.effect}</div>
      <div className="decree-card__cost">威权消耗: {meta.cost}</div>
      <button
        className="btn btn--primary"
        style={{ marginTop: '10px', width: '100%', fontSize: '12px' }}
        onClick={() => onIssue(decreeType)}
      >
        发布
      </button>
    </div>
  )
}
