/* =============================================
   EdictModal - v2.2.0 借鉴明末: 3 阶段诏书流程
   - 草稿池 (DecreeReviewPanel 内嵌)
   - 拟诏 / 颁布 (SSE 流式)
   - 退朝不下旨 (跳过)
   - 完成后 SettlementLock 显示
   ============================================= */
import { useState, useEffect, useRef, useCallback } from 'react'
import { X, Send, Lock, Unlock, FileText, Trash2, Edit3, Check, XCircle, ArrowRight } from 'lucide-react'
import { SettlementLock } from './SettlementLock'
import { api, IS_DEMO } from '../api'

interface Directive {
  id: number
  kind: string
  content: string
  status: 'draft' | 'confirmed' | 'rejected' | 'expired' | 'issued'
  turn: number
  year: number
  period: number
  created_at: string
}

interface EdictModalProps {
  isOpen: boolean
  onClose: () => void
  campaignId: string
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  draft: { label: '草稿', color: '#f59e0b' },
  confirmed: { label: '已批准', color: '#22c55e' },
  rejected: { label: '已驳回', color: '#ef4444' },
  expired: { label: '已过期', color: '#6b7280' },
  issued: { label: '已颁诏', color: '#3b82f6' },
}

export function EdictModal({ isOpen, onClose, campaignId }: EdictModalProps) {
  // 草案池
  const [directives, setDirectives] = useState<Directive[]>([])
  const [loading, setLoading] = useState(false)
  const [newText, setNewText] = useState('')
  const [newKind, setNewKind] = useState('颁布新政')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingText, setEditingText] = useState('')

  // SSE 推演态
  const [settling, setSettling] = useState(false)
  const [stage, setStage] = useState('')
  const [thinking, setThinking] = useState('')
  const [narrative, setNarrative] = useState('')
  const [decree, setDecree] = useState('')
  const [report, setReport] = useState<any>(null)
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previewText, setPreviewText] = useState<string | null>(null)
  const [previewing, setPreviewing] = useState(false)

  // 加载草案
  const fetchDirectives = useCallback(async () => {
    if (!campaignId) return
    setLoading(true)
    try {
      const data = await api<{ directives: Directive[] }>(`/api/campaigns/${campaignId}/directives`)
      setDirectives(data.directives || [])
    } catch (e) {
      console.error('加载草案失败', e)
    } finally {
      setLoading(false)
    }
  }, [campaignId])

  useEffect(() => {
    if (isOpen) fetchDirectives()
  }, [isOpen, fetchDirectives])

  // 新增草稿
  const handleCreate = async () => {
    if (!newText.trim()) return
    try {
      await api(`/api/campaigns/${campaignId}/directives`, {
        method: 'POST',
        body: JSON.stringify({ text: newText.trim(), kind: newKind, type: 'domestic' }),
      })
      setNewText('')
      fetchDirectives()
    } catch (e) {
      console.error('新增草案失败', e)
    }
  }

  // 删除草案
  const handleDelete = async (id: number) => {
    try {
      await api(`/api/campaigns/${campaignId}/directives/${id}`, { method: 'DELETE' })
      fetchDirectives()
    } catch (e) {
      console.error('删除草案失败', e)
    }
  }

  // 批准草案
  const handleConfirm = async (id: number) => {
    try {
      await api(`/api/campaigns/${campaignId}/directives/${id}/confirm`, { method: 'PUT' })
      fetchDirectives()
    } catch (e) {
      console.error('批准草案失败', e)
    }
  }

  // 驳回草案
  const handleReject = async (id: number) => {
    try {
      await api(`/api/campaigns/${campaignId}/directives/${id}/reject`, { method: 'PUT' })
      fetchDirectives()
    } catch (e) {
      console.error('驳回草案失败', e)
    }
  }

  // 修改草案
  const handleEdit = (d: Directive) => {
    setEditingId(d.id)
    setEditingText(d.content)
  }
  const handleSaveEdit = async (id: number) => {
    try {
      await api(`/api/campaigns/${campaignId}/directives/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ text: editingText.trim() }),
      })
      setEditingId(null)
      setEditingText('')
      fetchDirectives()
    } catch (e) {
      console.error('修改草案失败', e)
    }
  }

  // 拟诏 (调 /decree/write)
  const handlePreview = async () => {
    setPreviewing(true)
    try {
      const data = await api<{ decree_text: string }>(`/api/decree/write`, {
        method: 'POST',
        body: JSON.stringify({ campaign_id: campaignId }),
      })
      setPreviewText(data.decree_text || '（无）')
    } catch (e: any) {
      setPreviewText(`拟诏失败: ${e.message || e}`)
    } finally {
      setPreviewing(false)
    }
  }

  // SSE 流式颁诏
  const handleIssue = async () => {
    setSettling(true)
    setStage('')
    setThinking('')
    setNarrative('')
    setDecree('')
    setReport(null)
    setDone(false)
    setError(null)
    // v2.2.0 GitHub Pages 演示模式: 模拟 SSE 流
    if (IS_DEMO) {
      const mockStages = ['稽首', '明诏', '颁旨', '回奏']
      const mockDecree = '朕以大汉天子之名, 诏曰: 讨逆兴汉, 天下共举。'
      const mockReport = { result: '成功', cost: '银 5 万两', hidden: '无' }
      for (let i = 0; i < mockStages.length; i++) {
        setStage(mockStages[i])
        await new Promise(r => setTimeout(r, 300))
      }
      setDecree(mockDecree)
      setReport(mockReport)
      setDone(true)
      setSettling(false)
      return
    }
    try {
      const response = await fetch('/api/decree/issue/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaign_id: campaignId }),
      })
      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let failed = ''
      while (true) {
        const { value, done: streamDone } = await reader.read()
        if (streamDone) break
        buffer += decoder.decode(value, { stream: true })
        const blocks = buffer.split('\n\n')
        buffer = blocks.pop() || ''
        for (const block of blocks) {
          let evName = ''
          let dataRaw = ''
          for (const line of block.split('\n')) {
            if (line.startsWith('event: ')) evName = line.slice(7).trim()
            else if (line.startsWith('data: ')) dataRaw += line.slice(6)
          }
          if (!evName || !dataRaw) continue
          let data: any
          try { data = JSON.parse(dataRaw) } catch { continue }
          if (evName === 'stage') {
            setStage(data.content || '')
          } else if (evName === 'thinking') {
            setThinking((p) => p + (data.content || ''))
          } else if (evName === 'text') {
            setNarrative((p) => p + (data.content || ''))
          } else if (evName === 'error') {
            failed = data.message || '颁诏失败'
            setError(failed)
            setSettling(false)
            break
          } else if (evName === 'done') {
            setDecree(data.decree || '')
            setReport(data.report || {})
            setDone(true)
            fetchDirectives()
            return
          }
        }
      }
      if (failed) {
        setError(failed)
      }
    } catch (e: any) {
      setError(e.message || String(e))
      setSettling(false)
    }
  }

  // 退朝不下旨
  const handleAdvance = async () => {
    setSettling(true)
    setStage('')
    setThinking('')
    setNarrative('')
    setDecree('')
    setReport(null)
    setDone(false)
    setError(null)
    // v2.2.0 GitHub Pages 演示模式: 模拟推演
    if (IS_DEMO) {
      const mockStages = ['朝议', '廷推', '退朝']
      const mockNarrative = '是日朝会, 群臣议论纷纷, 然未有定策, 乃退朝。'
      for (const s of mockStages) {
        setStage(s)
        await new Promise(r => setTimeout(r, 300))
      }
      setNarrative(mockNarrative)
      setDone(true)
      setSettling(false)
      return
    }
    try {
      const response = await fetch('/api/decree/advance/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaign_id: campaignId }),
      })
      if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`)
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { value, done: streamDone } = await reader.read()
        if (streamDone) break
        buffer += decoder.decode(value, { stream: true })
        const blocks = buffer.split('\n\n')
        buffer = blocks.pop() || ''
        for (const block of blocks) {
          let evName = ''
          let dataRaw = ''
          for (const line of block.split('\n')) {
            if (line.startsWith('event: ')) evName = line.slice(7).trim()
            else if (line.startsWith('data: ')) dataRaw += line.slice(6)
          }
          if (!evName || !dataRaw) continue
          let data: any
          try { data = JSON.parse(dataRaw) } catch { continue }
          if (evName === 'stage') setStage(data.content || '')
          else if (evName === 'thinking') setThinking((p) => p + (data.content || ''))
          else if (evName === 'text') setNarrative((p) => p + (data.content || ''))
          else if (evName === 'error') {
            setError(data.message || '退朝失败')
            setSettling(false)
            return
          } else if (evName === 'done') {
            setDecree(data.decree || '')
            setReport(data.report || {})
            setDone(true)
            return
          }
        }
      }
    } catch (e: any) {
      setError(e.message || String(e))
      setSettling(false)
    }
  }

  // 关闭 SettlementLock
  const handleSettleClose = () => {
    setSettling(false)
    setStage(''); setThinking(''); setNarrative('')
    setDecree(''); setReport(null); setDone(false); setError(null)
    onClose()
  }

  if (!isOpen) return null

  const confirmedCount = directives.filter(d => d.status === 'confirmed').length

  return (
    <>
      <div className="modal-overlay" onClick={onClose}>
        <div className="edict-modal" onClick={e => e.stopPropagation()}>
          <div className="edict-modal__header">
            <h2 className="edict-modal__title">📜 诏书 · 本月指令</h2>
            <button className="edict-modal__close" onClick={onClose}>
              <X size={20} />
            </button>
          </div>

          <div className="edict-modal__body">
            {/* 草稿池 */}
            <div className="edict-section">
              <h3>📝 草稿池 ({directives.length} 道 · 已批准 {confirmedCount})</h3>
              {loading ? (
                <div className="edict-loading">加载中…</div>
              ) : directives.length === 0 ? (
                <div className="edict-empty">本月尚无指令，可在下方面板新增</div>
              ) : (
                <ul className="edict-list">
                  {directives.map(d => {
                    const s = STATUS_LABELS[d.status] || STATUS_LABELS.draft
                    return (
                      <li key={d.id} className="edict-item" style={{ borderLeftColor: s.color }}>
                        <div className="edict-item-head">
                          <span className="edict-item-kind">{d.kind}</span>
                          <span className="edict-item-status" style={{ color: s.color }}>{s.label}</span>
                        </div>
                        {editingId === d.id ? (
                          <div className="edict-item-edit">
                            <textarea
                              value={editingText}
                              onChange={e => setEditingText(e.target.value)}
                              rows={2}
                            />
                            <button className="btn btn--sm btn--primary" onClick={() => handleSaveEdit(d.id)}>
                              <Check size={12} /> 保存
                            </button>
                            <button className="btn btn--sm" onClick={() => setEditingId(null)}>
                              <XCircle size={12} /> 取消
                            </button>
                          </div>
                        ) : (
                          <div className="edict-item-body">
                            {d.content || '（空）'}
                          </div>
                        )}
                        <div className="edict-item-actions">
                          {d.status === 'draft' && (
                            <>
                              <button className="btn btn--sm" onClick={() => handleEdit(d)}>
                                <Edit3 size={12} /> 改
                              </button>
                              <button className="btn btn--sm btn--success" onClick={() => handleConfirm(d.id)}>
                                <Check size={12} /> 批准
                              </button>
                              <button className="btn btn--sm btn--danger" onClick={() => handleReject(d.id)}>
                                <XCircle size={12} /> 驳回
                              </button>
                            </>
                          )}
                          <button className="btn btn--sm btn--danger" onClick={() => handleDelete(d.id)}>
                            <Trash2 size={12} /> 删
                          </button>
                        </div>
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>

            {/* 新增草稿 */}
            <div className="edict-section edict-section--create">
              <h3>✍️ 拟写新指令</h3>
              <div className="edict-create-row">
                <select
                  className="edict-create-kind"
                  value={newKind}
                  onChange={e => setNewKind(e.target.value)}
                >
                  <option value="颁布新政">📜 颁布新政</option>
                  <option value="赈济灾民">🌾 赈济灾民</option>
                  <option value="兴兵讨伐">⚔️ 兴兵讨伐</option>
                  <option value="安抚百姓">🕊️ 安抚百姓</option>
                  <option value="整饬吏治">⚖️ 整饬吏治</option>
                  <option value="减免赋税">💰 减免赋税</option>
                </select>
                <textarea
                  className="edict-create-text"
                  value={newText}
                  onChange={e => setNewText(e.target.value)}
                  placeholder="指令内容 (如: 黄河决堤, 速开仓赈济)..."
                  rows={2}
                />
                <button className="btn btn--primary" onClick={handleCreate} disabled={!newText.trim()}>
                  <FileText size={14} /> 入草稿
                </button>
              </div>
            </div>

            {/* 拟诏预览 */}
            {previewText !== null && (
              <div className="edict-section edict-section--preview">
                <h3>👀 拟诏预览</h3>
                <pre className="edict-preview-box">{previewText}</pre>
              </div>
            )}
          </div>

          <div className="edict-modal__footer">
            <button className="btn" onClick={onClose}>取消</button>
            <button
              className="btn"
              onClick={handlePreview}
              disabled={previewing || confirmedCount === 0}
              title={confirmedCount === 0 ? '需先批准至少 1 道草案' : ''}
            >
              <FileText size={14} /> {previewing ? '拟诏中…' : '拟诏预览'}
            </button>
            <button
              className="btn"
              onClick={handleAdvance}
              title="本月退朝, 不下旨, 仅推演月结"
            >
              🚪 退朝
            </button>
            <button
              className="btn btn--primary"
              onClick={handleIssue}
              disabled={confirmedCount === 0}
              title={confirmedCount === 0 ? '需先批准至少 1 道草案' : ''}
            >
              <Send size={14} /> 颁布 ({confirmedCount})
            </button>
          </div>
        </div>
      </div>

      {settling && (
        <SettlementLock
          stage={stage}
          thinking={thinking}
          narrative={narrative}
          decree={decree}
          report={report}
          done={done}
          error={error || undefined}
          onClose={handleSettleClose}
        />
      )}
    </>
  )
}
