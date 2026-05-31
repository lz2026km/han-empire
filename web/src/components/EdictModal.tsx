import { useState } from 'react'
import { X, Eye, Send, Lock, Unlock } from 'lucide-react'

interface EdictModalProps {
  isOpen: boolean
  onClose: () => void
  onPublish: (content: string, isSecret: boolean) => Promise<void>
  edictTypes: { id: string; name: string; description: string; authorityCost: number }[]
}

export function EdictModal({ isOpen, onClose, onPublish, edictTypes }: EdictModalProps) {
  const [selectedType, setSelectedType] = useState<string>('')
  const [content, setContent] = useState('')
  const [isSecret, setIsSecret] = useState(false)
  const [preview, setPreview] = useState(false)
  const [publishing, setPublishing] = useState(false)

  const currentType = edictTypes.find(t => t.id === selectedType)

  const handlePublish = async () => {
    if (!content.trim() || !selectedType) return
    setPublishing(true)
    try {
      await onPublish(content, isSecret)
      setContent('')
      setSelectedType('')
      setIsSecret(false)
      setPreview(false)
      onClose()
    } catch (e) {
      console.error('Failed to publish edict:', e)
    }
    setPublishing(false)
  }

  const handleClose = () => {
    setContent('')
    setSelectedType('')
    setIsSecret(false)
    setPreview(false)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="edict-modal" onClick={e => e.stopPropagation()}>
        <div className="edict-modal__header">
          <h2 className="edict-modal__title">📜 颁布诏书</h2>
          <button className="edict-modal__close" onClick={handleClose}>
            <X size={20} />
          </button>
        </div>

        <div className="edict-modal__body">
          <div className="edict-modal__types">
            <div className="edict-modal__section-title">诏书类型</div>
            <div className="edict-modal__type-grid">
              {edictTypes.map(type => (
                <button
                  key={type.id}
                  className={`edict-modal__type ${selectedType === type.id ? 'edict-modal__type--selected' : ''}`}
                  onClick={() => setSelectedType(type.id)}
                >
                  <div className="edict-modal__type-name">{type.name}</div>
                  <div className="edict-modal__type-cost">消耗 {type.authorityCost} 威权</div>
                </button>
              ))}
            </div>
          </div>

          {currentType && (
            <div className="edict-modal__type-desc">
              {currentType.description}
            </div>
          )}

          <div className="edict-modal__options">
            <label className="edict-modal__secret-toggle">
              <input
                type="checkbox"
                checked={isSecret}
                onChange={e => setIsSecret(e.target.checked)}
              />
              <span className="edict-modal__secret-label">
                {isSecret ? <Lock size={14} /> : <Unlock size={14} />}
                {isSecret ? '密令（仅指定人可见）' : '明诏（公示天下）'}
              </span>
            </label>
          </div>

          {preview ? (
            <div className="edict-modal__preview">
              <div className="edict-modal__preview-header">
                <span className="edict-modal__preview-title">【御笔亲制】</span>
                {isSecret && <span className="edict-modal__preview-secret">密</span>}
              </div>
              <div className="edict-modal__preview-content">
                {content || '（空）'}
              </div>
              <div className="edict-modal__preview-footer">
                皇帝制曰：{currentType?.name || '诏'}
              </div>
            </div>
          ) : (
            <div className="edict-modal__editor">
              <textarea
                className="edict-modal__textarea"
                value={content}
                onChange={e => setContent(e.target.value)}
                placeholder="在此输入诏书内容..."
                rows={8}
              />
            </div>
          )}

          <div className="edict-modal__preview-toggle">
            <button
              className="btn"
              onClick={() => setPreview(!preview)}
            >
              <Eye size={16} />
              {preview ? '编辑' : '预览'}
            </button>
          </div>
        </div>

        <div className="edict-modal__footer">
          <button className="btn" onClick={handleClose}>
            取消
          </button>
          <button
            className="btn btn--primary"
            onClick={handlePublish}
            disabled={!content.trim() || !selectedType || publishing}
          >
            <Send size={16} />
            {publishing ? '发布中...' : '颁布诏书'}
          </button>
        </div>
      </div>
    </div>
  )
}