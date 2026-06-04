/* =============================================
   OrdersTab - v5.5.0+ 占位 (原 tabs/OrdersTab.tsx 已删, 临时桩)
   ============================================= */
interface OrdersTabProps {
  secretOrders?: any[]
  onRefresh?: () => void
  campaignId?: string
}

export function OrdersTab({ secretOrders }: OrdersTabProps) {
  return (
    <div className="tab-placeholder">
      <h2>密令</h2>
      <p>{secretOrders?.length ?? 0} 道密令</p>
      <p>暂未实现 (v5.5.0+ 临时占位, 原 tabs/OrdersTab.tsx 已合并到 StateModal)</p>
    </div>
  )
}
