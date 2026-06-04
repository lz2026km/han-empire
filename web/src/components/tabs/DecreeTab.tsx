/* =============================================
   DecreeTab - v5.5.0+ 占位 (原 tabs/DecreeTab.tsx 已删, 临时桩)
   ============================================= */
import type { GameState, MinisterStats } from '../../types'

interface DecreeTabProps {
  gameState: GameState | null
  ministers: MinisterStats[]
  onIssue?: (text: string) => void
}

export function DecreeTab(_props: DecreeTabProps) {
  return (
    <div className="tab-placeholder">
      <h2>诏令</h2>
      <p>暂未实现 (v5.5.0+ 临时占位, 原 tabs/DecreeTab.tsx 已合并到 EdictModal)</p>
    </div>
  )
}
