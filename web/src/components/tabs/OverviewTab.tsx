/* =============================================
   OverviewTab - v5.5.0+ 占位 (原 components/tabs/OverviewTab.tsx 已删, 临时桩)
   ============================================= */
import type { GameState, MinisterStats, FactionStats } from '../../types'

interface OverviewTabProps {
  gameState: GameState | null
  ministers: MinisterStats[]
  factions: FactionStats[]
  onNextTurn?: () => void
}

export function OverviewTab({ gameState }: OverviewTabProps) {
  return (
    <div className="tab-placeholder">
      <h2>国势总览</h2>
      <p>回合: {gameState?.turn ?? 0} · 年: {gameState?.year ?? 195}</p>
      <p>暂未实现 (v5.5.0+ 临时占位, 原 tabs/OverviewTab.tsx 已合并到 StateModal)</p>
    </div>
  )
}
