/* =============================================
   ConsortTab.tsx - 后宫系统 Tab (v1.17.0 Phase F)
   汉献帝之末路 - 后宫召幸 / 调教 / 衣带诏线索
   ============================================= */

import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '../api'
import type { Consort } from '../types'

interface ChatMessage {
  role: 'emperor' | 'consort'
  text: string
}

interface Props {
  campaignId: string
}

export function ConsortTab({ campaignId }: Props) {
  const [consorts, setConsorts] = useState<Consort[]>([])
  const [candidates, setCandidates] = useState<any[]>([])
  const [stats, setStats] = useState<any>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedConsort, setSelectedConsort] = useState<Consort | null>(null)
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([])
  const [inputMsg, setInputMsg] = useState('')
  const [audienceLoading, setAudienceLoading] = useState(false)
  const [cultivateSkill, setCultivateSkill] = useState('')
  const [cultivateTrait, setCultivateTrait] = useState('')
  const [cultivateWords, setCultivateWords] = useState('')
  const [cultivateResult, setCultivateResult] = useState<string | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)

  // 加载后宫名册
  const loadRoster = useCallback(async () => {
    if (!campaignId) return
    setLoading(true)
    setError(null)
    try {
      const data = await api.getConsortTab(campaignId)
      setConsorts(data.consorts || [])
      setCandidates(data.candidates || [])
      setStats(data.stats || {})
    } catch (e: any) {
      setError(`名册加载失败: ${e.message || e}`)
    } finally {
      setLoading(false)
    }
  }, [campaignId])

  useEffect(() => {
    loadRoster()
  }, [loadRoster])

  // 滚动到聊天末尾
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory])

  // 选妃嫔
  const handleSelectConsort = (c: Consort) => {
    setSelectedConsort(c)
    setChatHistory([])
    setCultivateResult(null)
    setCultivateSkill('')
    setCultivateTrait('')
  }

  // 召幸对话
  const handleAudience = async () => {
    if (!selectedConsort || !inputMsg.trim() || audienceLoading) return
    const userMsg = inputMsg.trim()
    setInputMsg('')
    setChatHistory(prev => [...prev, { role: 'emperor', text: userMsg }])
    setAudienceLoading(true)
    try {
      const res = await api.audienceConsort(campaignId, selectedConsort.id, userMsg)
      const reply = res.result || '（妃嫔沉默）'
      setChatHistory(prev => [...prev, { role: 'consort', text: reply }])
    } catch (e: any) {
      setChatHistory(prev => [...prev, { role: 'consort', text: `（召幸失败: ${e.message || e}）` }])
    } finally {
      setAudienceLoading(false)
    }
  }

  // 调教（学技能 / 改性格）
  const handleCultivate = async () => {
    if (!selectedConsort) return
    if (!cultivateSkill.trim() && !cultivateTrait.trim()) {
      setCultivateResult('请至少填写一项：新技能或新性格')
      return
    }
    if (!cultivateWords.trim()) {
      setCultivateResult('请填写皇帝教诲之言（emperor_words）')
      return
    }
    setCultivateResult(null)
    try {
      const res = await api.cultivateConsort(
        campaignId,
        selectedConsort.id,
        cultivateSkill.trim(),
        cultivateTrait.trim(),
        cultivateWords.trim()
      )
      if (res.ok) {
        setCultivateResult(`调教成功：${cultivateSkill || '（未改技能）'} + ${cultivateTrait || '（未改性格）'}`)
        setCultivateSkill('')
        setCultivateTrait('')
        setCultivateWords('')
        // 刷新名册
        await loadRoster()
      } else {
        setCultivateResult(`调教失败：${res.error || '未知错误'}`)
      }
    } catch (e: any) {
      setCultivateResult(`调教异常: ${e.message || e}`)
    }
  }

  if (loading) {
    return <div className="empty-state">后宫名册加载中…</div>
  }

  if (error) {
    return <div className="empty-state">⚠️ {error}</div>
  }

  return (
    <div className="fade-in consort-tab">
      <div style={{ marginBottom: '16px' }}>
        <h2 style={{ color: 'var(--color-gold)', marginBottom: '8px', fontSize: '20px' }}>
          🏯 后宫 ({stats.total_consorts || 0} 位妃嫔，{stats.total_candidates || 6} 位候选)
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px' }}>
          召幸妃嫔以固皇恩，调教其技能性格以应时势。密谋大事，请入衣带诏线。
        </p>
      </div>

      <div className="consort-grid">
        {/* 左：名册 */}
        <div className="consort-roster">
          <h3 className="section-title">📜 后宫名册</h3>
          {consorts.length === 0 && (
            <p style={{ color: 'var(--color-text-muted)', fontSize: '13px' }}>
              当前朝代尚无入宫妃嫔。可从下列候选人物中选招。
            </p>
          )}
          {consorts.map(c => (
            <div
              key={c.id}
              className={`consort-card ${selectedConsort?.id === c.id ? 'consort-card--selected' : ''}`}
              onClick={() => handleSelectConsort(c)}
            >
              <div className="consort-card__header">
                <span className="consort-card__name">{c.canonical_name || c.name}</span>
                <span className="consort-card__title">{c.title || c.rank || '妃'}</span>
              </div>
              <div className="consort-card__meta">
                <span className="consort-card__faction">{c.faction || '中立'}</span>
                <span className="consort-card__affinity">好感 {c.affinity ?? '—'}</span>
              </div>
              <div className="consort-card__personality">{c.personality || '性格未录'}</div>
              {c.skills && c.skills.length > 0 && (
                <div className="consort-card__skills">
                  技能：{c.skills.join(' · ')}
                </div>
              )}
            </div>
          ))}

          {consorts.length < 6 && candidates.length > 0 && (
            <details style={{ marginTop: '12px' }}>
              <summary style={{ color: 'var(--color-text-secondary)', cursor: 'pointer', fontSize: '13px' }}>
                候选人物 ({candidates.length})
              </summary>
              <div style={{ marginTop: '8px', padding: '8px', background: 'var(--color-bg-secondary)', borderRadius: '4px' }}>
                {candidates.map((cand: any) => (
                  <div key={cand.id} style={{ marginBottom: '4px', fontSize: '12px' }}>
                    <strong>{cand.canonical_name || cand.name}</strong>
                    <span style={{ color: 'var(--color-text-muted)' }}>
                      {' '}({cand.title} · {cand.faction})
                    </span>
                  </div>
                ))}
              </div>
            </details>
          )}
        </div>

        {/* 右：召幸 + 调教 */}
        <div className="consort-interact">
          {!selectedConsort ? (
            <div className="empty-state" style={{ padding: '40px 20px' }}>
              <div style={{ fontSize: '32px', marginBottom: '12px' }}>👆</div>
              <p>请从左侧选择一位妃嫔，开始召幸或调教</p>
            </div>
          ) : (
            <>
              <h3 className="section-title">💬 召幸 · {selectedConsort.canonical_name || selectedConsort.name}</h3>
              <div className="consort-chat">
                {chatHistory.length === 0 && (
                  <p style={{ color: 'var(--color-text-muted)', fontSize: '13px', textAlign: 'center', padding: '20px' }}>
                    （尚未开口）
                  </p>
                )}
                {chatHistory.map((msg, i) => (
                  <div key={i} className={`consort-msg consort-msg--${msg.role}`}>
                    <div className="consort-msg__role">
                      {msg.role === 'emperor' ? '👑 献帝' : `🏯 ${selectedConsort.canonical_name || selectedConsort.name}`}
                    </div>
                    <div className="consort-msg__text">{msg.text}</div>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>
              <div className="consort-input-row">
                <input
                  type="text"
                  value={inputMsg}
                  onChange={e => setInputMsg(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') handleAudience() }}
                  placeholder="陛下有何吩咐？"
                  disabled={audienceLoading}
                  style={{ flex: 1 }}
                />
                <button
                  className="btn btn--primary"
                  onClick={handleAudience}
                  disabled={audienceLoading || !inputMsg.trim()}
                >
                  {audienceLoading ? '…' : '传召'}
                </button>
              </div>

              <h3 className="section-title" style={{ marginTop: '20px' }}>📚 调教（学技能 / 改性格）</h3>
              <div className="consort-cultivate">
                <div className="consort-form-row">
                  <label>新技能</label>
                  <input
                    type="text"
                    value={cultivateSkill}
                    onChange={e => setCultivateSkill(e.target.value)}
                    placeholder="如：剑术初习"
                  />
                </div>
                <div className="consort-form-row">
                  <label>新性格</label>
                  <input
                    type="text"
                    value={cultivateTrait}
                    onChange={e => setCultivateTrait(e.target.value)}
                    placeholder="如：直率，胆气"
                  />
                </div>
                <div className="consort-form-row">
                  <label>教诲之言</label>
                  <textarea
                    value={cultivateWords}
                    onChange={e => setCultivateWords(e.target.value)}
                    placeholder="如：朕要你学剑术，将来护驾"
                    rows={2}
                  />
                </div>
                <button
                  className="btn btn--gold"
                  onClick={handleCultivate}
                  style={{ width: '100%', marginTop: '8px' }}
                >
                  ✍️ 颁下教诲
                </button>
                {cultivateResult && (
                  <div
                    className={cultivateResult.startsWith('调教成功') ? 'cultivate-result--ok' : 'cultivate-result--err'}
                    style={{ marginTop: '8px', padding: '8px', borderRadius: '4px', fontSize: '12px' }}
                  >
                    {cultivateResult}
                  </div>
                )}
              </div>

              <h3 className="section-title" style={{ marginTop: '20px' }}>🔐 衣带诏线索</h3>
              <div className="consort-secret" style={{
                padding: '12px',
                background: 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border)',
                borderRadius: '4px',
                fontSize: '12px',
                color: 'var(--color-text-secondary)',
              }}>
                <p style={{ marginBottom: '6px' }}>
                  汉献帝密谋多由后宫起——伏寿、董贵皆衣带诏主谋。
                </p>
                <p>
                  欲下密旨，请走「密令」Tab。
                  妃嫔若家族与该事相关（伏、董、何、曹），可在召幸中承旨。
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
