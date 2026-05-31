/* =============================================
   DecreeReviewPanel - React component for managing draft directives
   ============================================= */
import { useState, useEffect, useCallback } from 'react'

export interface Directive {
  id: number
  turn: number
  year: number
  period: number
  text: string
  source: string
  actor: string
  status: 'draft' | 'confirmed' | 'rejected' | 'expired'
  notes: string
  created_at: string
}

interface DecreeReviewPanelProps {
  campaignId: string
  apiBase?: string
  onRefresh?: () => void
}

const STATUS_COLORS: Record<string, string> = {
  draft: '#f59e0b',
  confirmed: '#22c55e',
  rejected: '#ef4444',
  expired: '#6b7280',
}

const STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  confirmed: '已批准',
  rejected: '已驳回',
  expired: '已过期',
}

export default function DecreeReviewPanel({ campaignId, apiBase = 'http://localhost:5555/api', onRefresh }: DecreeReviewPanelProps) {
  const [directives, setDirectives] = useState<Directive[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [newText, setNewText] = useState('')
  const [newActor, setNewActor] = useState('')
  const [newSource, setNewSource] = useState('')
  const [generatedDecree, setGeneratedDecree] = useState<string | null>(null)

  const fetchDirectives = useCallback(async () => {
    if (!campaignId) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${apiBase}/directives?campaign_id=${campaignId}`)
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setDirectives(data.directives || [])
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [campaignId, apiBase])

  useEffect(() => {
    fetchDirectives()
  }, [fetchDirectives])

  const handleConfirm = useCallback(async (id: number) => {
    try {
      const res = await fetch(`${apiBase}/directives/${id}/confirm`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaign_id: campaignId }),
      })
      if (!res.ok) throw new Error(await res.text())
      await fetchDirectives()
      onRefresh?.()
    } catch (e: any) {
      setError(e.message)
    }
  }, [campaignId, apiBase, fetchDirectives, onRefresh])

  const handleReject = useCallback(async (id: number) => {
    try {
      const res = await fetch(`${apiBase}/directives/${id}/reject`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaign_id: campaignId }),
      })
      if (!res.ok) throw new Error(await res.text())
      await fetchDirectives()
      onRefresh?.()
    } catch (e: any) {
      setError(e.message)
    }
  }, [campaignId, apiBase, fetchDirectives, onRefresh])

  const handleDelete = useCallback(async (id: number) => {
    if (!confirm('确定删除此草稿？')) return
    try {
      const res = await fetch(`${apiBase}/directives/${id}?campaign_id=${campaignId}`, {
        method: 'DELETE',
      })
      if (!res.ok) throw new Error(await res.text())
      await fetchDirectives()
      onRefresh?.()
    } catch (e: any) {
      setError(e.message)
    }
  }, [campaignId, apiBase, fetchDirectives, onRefresh])

  const handleAddDirective = useCallback(async () => {
    if (!newText.trim()) {
      setError('请输入指令内容')
      return
    }
    try {
      const res = await fetch(`${apiBase}/directives`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_id: campaignId,
          text: newText.trim(),
          actor: newActor.trim(),
          source: newSource.trim(),
        }),
      })
      if (!res.ok) throw new Error(await res.text())
      setNewText('')
      setNewActor('')
      setNewSource('')
      await fetchDirectives()
      onRefresh?.()
    } catch (e: any) {
      setError(e.message)
    }
  }, [campaignId, apiBase, newText, newActor, newSource, fetchDirectives, onRefresh])

  const handleWriteDecree = useCallback(async () => {
    const confirmed = directives.filter(d => d.status === 'confirmed')
    if (confirmed.length === 0) {
      setError('没有已批准的指令，无法生成正式诏书')
      return
    }
    try {
      const res = await fetch(`${apiBase}/decree/write`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaign_id: campaignId }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setGeneratedDecree(data.decree_text || data.result || '生成失败')
    } catch (e: any) {
      setError(e.message)
    }
  }, [campaignId, apiBase, directives])

  const draftDirectives = directives.filter(d => d.status === 'draft')
  const confirmedDirectives = directives.filter(d => d.status === 'confirmed')
  const otherDirectives = directives.filter(d => d.status !== 'draft' && d.status !== 'confirmed')

  return (
    <div style={{
      fontFamily: '"Noto Serif SC", "Songti SC", "STSong", "SimSun", serif',
      background: 'rgba(26, 26, 46, 0.95)',
      border: '1px solid rgba(74, 45, 20, 0.42)',
      borderRadius: 8,
      padding: 16,
      color: '#e8d5b7',
      minHeight: 400,
    }}>
      <h3 style={{ color: '#c9a96e', margin: '0 0 16px', fontSize: 18, borderBottom: '1px solid #2d2d44', paddingBottom: 8 }}>
        📜 诏令审议面板
      </h3>

      {error && (
        <div style={{ background: '#2d1f1f', border: '1px solid #ef4444', borderRadius: 6, padding: 8, marginBottom: 12, color: '#ef4444', fontSize: 13 }}>
          ❌ {error}
        </div>
      )}

      {loading && <div style={{ color: '#9ca3af', fontSize: 13 }}>加载中...</div>}

      {/* Draft Directives */}
      <div style={{ marginBottom: 20 }}>
        <h4 style={{ color: '#f59e0b', margin: '0 0 8px', fontSize: 14 }}>
          草稿指令（{draftDirectives.length}）
        </h4>
        {draftDirectives.length === 0 ? (
          <p style={{ color: '#6b7280', fontSize: 13 }}>暂无草稿指令</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {draftDirectives.map(d => (
              <div key={d.id} style={{
                background: '#1a1a2e',
                border: '1px solid #2d2d44',
                borderRadius: 6,
                padding: 10,
                borderLeft: `3px solid ${STATUS_COLORS[d.status]}`,
              }}>
                <div style={{ fontSize: 14, marginBottom: 4, color: '#e8d5b7' }}>{d.text}</div>
                <div style={{ display: 'flex', gap: 12, fontSize: 11, color: '#9ca3af', marginBottom: 8 }}>
                  {d.actor && <span>📌 {d.actor}</span>}
                  {d.source && <span>📋 {d.source}</span>}
                  <span>回合{d.turn}</span>
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button
                    onClick={() => handleConfirm(d.id)}
                    style={{
                      background: '#166534',
                      border: '1px solid #22c55e',
                      borderRadius: 4,
                      color: '#22c55e',
                      padding: '4px 10px',
                      fontSize: 12,
                      cursor: 'pointer',
                    }}
                  >
                    ✅ 批准
                  </button>
                  <button
                    onClick={() => handleReject(d.id)}
                    style={{
                      background: '#7f1d1d',
                      border: '1px solid #ef4444',
                      borderRadius: 4,
                      color: '#ef4444',
                      padding: '4px 10px',
                      fontSize: 12,
                      cursor: 'pointer',
                    }}
                  >
                    ❌ 驳回
                  </button>
                  <button
                    onClick={() => handleDelete(d.id)}
                    style={{
                      background: '#1f2937',
                      border: '1px solid #6b7280',
                      borderRadius: 4,
                      color: '#9ca3af',
                      padding: '4px 10px',
                      fontSize: 12,
                      cursor: 'pointer',
                    }}
                  >
                    🗑️ 删除
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Confirmed Directives */}
      {confirmedDirectives.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h4 style={{ color: '#22c55e', margin: '0 0 8px', fontSize: 14 }}>
            已批准指令（{confirmedDirectives.length}）
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {confirmedDirectives.map(d => (
              <div key={d.id} style={{
                background: '#1a1a2e',
                border: '1px solid #2d2d44',
                borderRadius: 6,
                padding: 10,
                borderLeft: '3px solid #22c55e',
              }}>
                <div style={{ fontSize: 14, marginBottom: 4, color: '#e8d5b7' }}>{d.text}</div>
                <div style={{ display: 'flex', gap: 12, fontSize: 11, color: '#9ca3af' }}>
                  {d.actor && <span>📌 {d.actor}</span>}
                  {d.source && <span>📋 {d.source}</span>}
                  <span>回合{d.turn}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Other status directives */}
      {otherDirectives.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h4 style={{ color: '#9ca3af', margin: '0 0 8px', fontSize: 14 }}>
            其他指令（{otherDirectives.length}）
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {otherDirectives.map(d => (
              <div key={d.id} style={{
                background: '#1a1a2e',
                border: '1px solid #2d2d44',
                borderRadius: 6,
                padding: 10,
                borderLeft: `3px solid ${STATUS_COLORS[d.status] || '#6b7280'}`,
                opacity: 0.7,
              }}>
                <div style={{ fontSize: 14, marginBottom: 4, color: '#9ca3af' }}>{d.text}</div>
                <div style={{ display: 'flex', gap: 12, fontSize: 11, color: '#6b7280' }}>
                  <span style={{ color: STATUS_COLORS[d.status] }}>{STATUS_LABELS[d.status]}</span>
                  <span>回合{d.turn}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add new directive */}
      <div style={{
        background: '#16213e',
        border: '1px solid #2d2d44',
        borderRadius: 6,
        padding: 12,
        marginBottom: 16,
      }}>
        <h4 style={{ color: '#c9a96e', margin: '0 0 10px', fontSize: 14 }}>➕ 添加新指令</h4>
        <textarea
          value={newText}
          onChange={e => setNewText(e.target.value)}
          placeholder="输入指令内容..."
          rows={3}
          style={{
            width: '100%',
            background: '#1a1a2e',
            border: '1px solid #2d2d44',
            borderRadius: 4,
            color: '#e8d5b7',
            fontSize: 13,
            padding: 8,
            resize: 'vertical',
            fontFamily: 'inherit',
            boxSizing: 'border-box',
            marginBottom: 8,
          }}
        />
        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <input
            value={newActor}
            onChange={e => setNewActor(e.target.value)}
            placeholder="发起人（可选）"
            style={{
              flex: 1,
              background: '#1a1a2e',
              border: '1px solid #2d2d44',
              borderRadius: 4,
              color: '#e8d5b7',
              fontSize: 13,
              padding: '6px 8px',
              fontFamily: 'inherit',
            }}
          />
          <input
            value={newSource}
            onChange={e => setNewSource(e.target.value)}
            placeholder="来源（可选）"
            style={{
              flex: 1,
              background: '#1a1a2e',
              border: '1px solid #2d2d44',
              borderRadius: 4,
              color: '#e8d5b7',
              fontSize: 13,
              padding: '6px 8px',
              fontFamily: 'inherit',
            }}
          />
        </div>
        <button
          onClick={handleAddDirective}
          disabled={!newText.trim()}
          style={{
            background: newText.trim() ? '#8b0000' : '#2d2d44',
            border: '1px solid #c9a96e',
            borderRadius: 4,
            color: '#e8d5b7',
            padding: '6px 16px',
            fontSize: 13,
            cursor: newText.trim() ? 'pointer' : 'not-allowed',
            fontFamily: 'inherit',
          }}
        >
          ➕ 添加草稿
        </button>
      </div>

      {/* Write Decree button */}
      <button
        onClick={handleWriteDecree}
        disabled={confirmedDirectives.length === 0}
        style={{
          background: confirmedDirectives.length > 0 ? 'linear-gradient(135deg, #8b0000 0%, #5c0000 100%)' : '#2d2d44',
          border: '1px solid #c9a96e',
          borderRadius: 6,
          color: '#e8d5b7',
          padding: '10px 20px',
          fontSize: 14,
          cursor: confirmedDirectives.length > 0 ? 'pointer' : 'not-allowed',
          fontFamily: 'inherit',
          width: '100%',
          fontWeight: 'bold',
        }}
      >
        📜 生成正式诏书（{confirmedDirectives.length}条已批准）
      </button>

      {/* Generated decree display */}
      {generatedDecree && (
        <div style={{
          background: 'rgba(232, 224, 205, 0.95)',
          border: '1px solid rgba(0,0,0,0.2)',
          borderRadius: 8,
          padding: '12px 16px',
          marginTop: 12,
          color: '#1a1410',
          fontSize: 14,
          lineHeight: 1.8,
          whiteSpace: 'pre-wrap',
          boxShadow: '0 4px 14px rgba(0,0,0,0.3)',
        }}>
          <div style={{ fontWeight: 'bold', color: '#8a221a', marginBottom: 8, fontSize: 15 }}>【正式诏书】</div>
          {generatedDecree}
        </div>
      )}
    </div>
  )
}