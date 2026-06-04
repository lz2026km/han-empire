// v2.0.0 Phase 3.1: 密诏 Tab - 抽自 App.tsx:897-927 (31 行)
// 汉风命名（原"密令")—— 衣带诏是东汉三国著名政治事件
import { useEffect } from 'react'
import type { SecretOrder } from '../../api'

export function OrdersTab({ secretOrders, onRefresh }: { secretOrders: SecretOrder[]; onRefresh: () => void }) {
  // v2.0.0 P0-B3: onRefresh 已 useCallback 稳定引用，不会再触发死循环
  useEffect(() => {
    onRefresh()
  }, [onRefresh])

  return (
    <div className="fade-in">
      <div className="card">
        <div style={{ marginBottom: '16px', color: 'var(--color-gold)' }}>密诏追踪</div>
        {secretOrders.length === 0 ? (
          <div className="empty-state">暂无密诏</div>
        ) : (
          <div>
            {secretOrders.map(order => (
              <div key={order.id} className="secret-order" style={{ marginBottom: '12px' }}>
                <div className="secret-order__header">
                  <span className="secret-order__title">{order.title}</span>
                  <span className="secret-order__status">{order.status}</span>
                </div>
                <div className="secret-order__meta">
                  <span>对象: {order.targetName}</span>
                  <span>{order.issuedAt}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}