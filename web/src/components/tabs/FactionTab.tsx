/* =============================================
   FactionTab - v5.5.0+ 占位 (原 tabs/FactionTab.tsx 已删, 临时桩)
   ============================================= */
import type { FactionStats } from '../../types'

interface FactionTabProps {
  factions: FactionStats[]
}

export function FactionTab({ factions }: FactionTabProps) {
  return (
    <div className="tab-placeholder">
      <h2>派系</h2>
      <p>共 {factions.length} 派</p>
      <p>暂未实现 (v5.5.0+ 临时占位, 原 tabs/FactionTab.tsx 已合并到 StateModal)</p>
    </div>
  )
}
