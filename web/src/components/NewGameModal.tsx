/* =============================================
   NewGameModal - 通用建新朝弹窗 (v5.2.0 P6-3)
   抽自 App.tsx 内联版本, 现作为可复用组件
   用法: 游戏中按"主菜单"返回后想建新朝 / 重新开局
   ============================================= */
import { useState } from 'react'
import { Plus } from 'lucide-react'

interface NewGameModalProps {
  open: boolean
  loading?: boolean
  defaultName?: string
  onConfirm: (emperorName: string) => void | Promise<void>
  onCancel: () => void
}

export function NewGameModal({ open, loading, defaultName = '刘协', onConfirm, onCancel }: NewGameModalProps) {
  const [emperorName, setEmperorName] = useState(defaultName)

  if (!open) return null

  const handleSubmit = async () => {
    await onConfirm(emperorName.trim() || defaultName)
  }

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal__title">建立新朝</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label
              style={{
                display: 'block', marginBottom: '6px',
                color: 'var(--color-text-secondary)', fontSize: '13px',
              }}
            >
              皇帝名 (默认 {defaultName})
            </label>
            <input
              type="text"
              value={emperorName}
              onChange={e => setEmperorName(e.target.value)}
              style={{ width: '100%' }}
              placeholder={defaultName}
              disabled={loading}
              autoFocus
            />
          </div>
          <div
            style={{
              fontSize: '11px',
              color: 'var(--color-text-muted)',
              lineHeight: 1.6,
              fontStyle: 'italic',
            }}
          >
            主公将以献帝之身, 在 189-220 年的乱局中求存。<br />
            通过诏书、派系、技能和建筑, 一步步夺回皇权。
          </div>
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
            <button type="button" className="btn" onClick={onCancel} disabled={loading}>
              取消
            </button>
            <button
              type="button"
              className="btn btn--primary"
              onClick={handleSubmit}
              disabled={loading}
            >
              <Plus size={14} /> {loading ? '创建中...' : '建立朝代'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
