import { useState, useEffect } from 'react'
import { X, Eye, EyeOff, Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'

interface SecretOrder {
  id: string
  title: string
  content: string
  targetName: string
  issuedAt: string
  status: 'pending' | 'executing' | 'completed' | 'failed' | 'exposed'
  result?: string
}

interface SecretOrdersModalProps {
  isOpen: boolean
  onClose: () => void
  orders: SecretOrder[]
  onCancelOrder?: (orderId: string) => void
}

export function SecretOrdersModal({ isOpen, onClose, orders, onCancelOrder }: SecretOrdersModalProps) {
  const [selectedOrder, setSelectedOrder] = useState<SecretOrder | null>(null)
  const [showCompleted, setShowCompleted] = useState(false)

  // W2: Escape 关闭支持 (v3.3 UX 大修)
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  // W2: 打开时焦点陷阱 — 锁定 body 滚动
  useEffect(() => {
    if (isOpen) {
      const orig = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => { document.body.style.overflow = orig; };
    }
  }, [isOpen]);

  const filteredOrders = showCompleted
    ? orders
    : orders.filter(o => o.status !== 'completed' && o.status !== 'failed')

  const getStatusIcon = (status: SecretOrder['status']) => {
    switch (status) {
      case 'pending':
        return <Clock size={14} className="secret-order__status-icon secret-order__status-icon--pending" />
      case 'executing':
        return <AlertTriangle size={14} className="secret-order__status-icon secret-order__status-icon--executing" />
      case 'completed':
        return <CheckCircle size={14} className="secret-order__status-icon secret-order__status-icon--completed" />
      case 'failed':
        return <XCircle size={14} className="secret-order__status-icon secret-order__status-icon--failed" />
      case 'exposed':
        return <Eye size={14} className="secret-order__status-icon secret-order__status-icon--exposed" />
      default:
        return null
    }
  }

  const getStatusText = (status: SecretOrder['status']) => {
    switch (status) {
      case 'pending': return '待执行'
      case 'executing': return '执行中'
      case 'completed': return '已完成'
      case 'failed': return '已失败'
      case 'exposed': return '已败露'
      default: return status
    }
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="secret-orders-modal" onClick={e => e.stopPropagation()}>
        <div className="secret-orders-modal__header">
          <h2 className="secret-orders-modal__title">
            密令 密令追踪
          </h2>
          <label className="secret-orders-modal__toggle">
            <input
              type="checkbox"
              checked={showCompleted}
              onChange={e => setShowCompleted(e.target.checked)}
            />
            <span>显示已完成</span>
          </label>
          <button type="button" className="secret-orders-modal__close" onClick={onClose} aria-label="关闭密令">
            <X size={20} />
          </button>
        </div>

        <div className="secret-orders-modal__body">
          <div className="secret-orders-modal__list">
            {filteredOrders.length === 0 ? (
              <div className="secret-orders-modal__empty">
                <AlertTriangle size={32} strokeWidth={1} />
                <p>暂无密令记录</p>
                <p className="secret-orders-modal__empty-hint">密令可通过召对大臣或特定诏书发布</p>
              </div>
            ) : (
              filteredOrders.map(order => (
                <div
                  key={order.id}
                  className={`secret-order ${selectedOrder?.id === order.id ? 'secret-order--selected' : ''}`}
                  onClick={() => setSelectedOrder(order)} role="button" tabIndex={0}
                >
                  <div className="secret-order__header">
                    <span className="secret-order__title">{order.title}</span>
                    <span className="secret-order__status">
                      {getStatusIcon(order.status)}
                      {getStatusText(order.status)}
                    </span>
                  </div>
                  <div className="secret-order__meta">
                    <span>对象: {order.targetName}</span>
                    <span>{order.issuedAt}</span>
                  </div>
                  {order.status === 'exposed' && (
                    <div className="secret-order__warning">
                      [警告]️ 此密令已被发现，可能影响大臣忠诚
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {selectedOrder && (
            <div className="secret-orders-modal__detail">
              <div className="secret-order__detail-header">
                <h3>{selectedOrder.title}</h3>
                <span className={`secret-order__status secret-order__status--${selectedOrder.status}`}>
                  {getStatusIcon(selectedOrder.status)}
                  {getStatusText(selectedOrder.status)}
                </span>
              </div>
              <div className="secret-order__detail-content">
                <div className="secret-order__detail-label">密令内容</div>
                <div className="secret-order__detail-text">{selectedOrder.content}</div>
              </div>
              <div className="secret-order__detail-info">
                <div>执行人: {selectedOrder.targetName}</div>
                <div>发布时间: {selectedOrder.issuedAt}</div>
              </div>
              {selectedOrder.result && (
                <div className="secret-order__detail-result">
                  <div className="secret-order__detail-label">执行结果</div>
                  <div className="secret-order__detail-text">{selectedOrder.result}</div>
                </div>
              )}
              {(selectedOrder.status === 'pending' || selectedOrder.status === 'executing') && onCancelOrder && (
                <button type="button"
                  className="btn secret-order__cancel"
                  onClick={() => {
                    onCancelOrder(selectedOrder.id)
                    setSelectedOrder(null)
                  }}
                >
                  取消密令
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}