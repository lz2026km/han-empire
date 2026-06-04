/* =============================================
   MinisterTab - v5.5.0+ 占位 (原 tabs/MinisterTab.tsx 已删, 临时桩)
   ============================================= */
import type { MinisterStats } from '../../types'

interface MinisterTabProps {
  ministers: MinisterStats[]
}

export function MinisterTab({ ministers }: MinisterTabProps) {
  return (
    <div className="tab-placeholder">
      <h2>群臣</h2>
      <p>共 {ministers.length} 位大臣</p>
      <p>暂未实现 (v5.5.0+ 临时占位, 原 tabs/MinisterTab.tsx 已合并到 StateModal)</p>
    </div>
  )
}
