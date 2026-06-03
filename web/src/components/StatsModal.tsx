/* =============================================
   StatsModal - 多周目统计弹窗 (v5.2.0 P6-8)
   调 /api/stats/global + /api/stats/runs, 显示 5 卡 + 历史表
   ============================================= */
import { useEffect, useState } from 'react'
import { Trophy, Skull, TrendingUp, Award, History } from 'lucide-react'
import { api } from '../api'

interface StatsModalProps {
  open: boolean
  onClose: () => void
}

const ENDING_COLOR: Record<string, string> = {
  中兴: '#5bbf6b',
  议和: '#5b8fb9',
  禅让: '#a89b82',
  南迁: '#d4a017',
  衣带诏: '#c42b2b',
  流亡: '#8a7034',
  崩盘: '#c42b2b',
}

export function StatsModal({ open, onClose }: StatsModalProps) {
  const [global, setGlobal] = useState<any>(null)
  const [runs, setRuns] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  useEffect(() => {
    if (!open) return
    setLoading(true)
    Promise.all([
      api.getStatsGlobal().catch(() => null),
      api.getStatsRuns(20).catch(() => ({ runs: [] })),
    ]).then(([g, r]) => {
      setGlobal(g)
      setRuns(r?.runs || [])
      setLoading(false)
    })
  }, [open])

  if (!open) return null

  const winRate = global && global.total_runs > 0
    ? Math.round((global.wins / global.total_runs) * 100) : 0
  const avgTurns = global && global.total_runs > 0
    ? Math.round(global.total_turns / global.total_runs) : 0

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '720px', maxHeight: '85vh' }}>
        <div className="modal__title">
          <Trophy size={16} style={{ verticalAlign: 'middle', marginRight: 6 }} />
          多周目统计
        </div>

        {loading && <p style={{ color: 'var(--color-text-muted)' }}>加载中...</p>}

        {!loading && global && (
          <>
            {/* 5 卡 */}
            <div className="stats-grid">
              <div className="stats-card">
                <div className="stats-card__icon stats-card__icon--gold">
                  <History size={20} />
                </div>
                <div className="stats-card__label">总局数</div>
                <div className="stats-card__value">{global.total_runs}</div>
              </div>
              <div className="stats-card">
                <div className="stats-card__icon" style={{ background: 'rgba(91,191,107,0.15)', color: '#5bbf6b' }}>
                  <Trophy size={20} />
                </div>
                <div className="stats-card__label">胜率</div>
                <div className="stats-card__value">{winRate}%</div>
                <div className="stats-card__sub">胜 {global.wins} / 负 {global.losses}</div>
              </div>
              <div className="stats-card">
                <div className="stats-card__icon" style={{ background: 'rgba(196,43,43,0.15)', color: '#c42b2b' }}>
                  <Skull size={20} />
                </div>
                <div className="stats-card__label">败局</div>
                <div className="stats-card__value">{global.losses}</div>
              </div>
              <div className="stats-card">
                <div className="stats-card__icon stats-card__icon--gold">
                  <TrendingUp size={20} />
                </div>
                <div className="stats-card__label">平均回合</div>
                <div className="stats-card__value">{avgTurns}</div>
              </div>
              <div className="stats-card">
                <div className="stats-card__icon stats-card__icon--gold">
                  <Award size={20} />
                </div>
                <div className="stats-card__label">结局解锁</div>
                <div className="stats-card__value">{global.endings_unlocked?.length || 0} / 7</div>
                <div className="stats-card__sub">
                  {(global.endings_unlocked || []).join(' / ') || '尚未解锁'}
                </div>
              </div>
            </div>

            {/* 历史 */}
            <h3 style={{ margin: '18px 0 8px', color: 'var(--color-gold)', fontSize: '14px' }}>
              最近 {runs.length} 局
            </h3>
            <div className="stats-history">
              {runs.length === 0 ? (
                <p style={{ color: 'var(--color-text-muted)', fontSize: '12px' }}>
                  暂无历史, 完成首局后可见
                </p>
              ) : (
                <table className="stats-table">
                  <thead>
                    <tr>
                      <th>序号</th>
                      <th>战役</th>
                      <th>结局</th>
                      <th>回合</th>
                      <th>得分</th>
                      <th>时间</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.map((r, i) => (
                      <tr key={r.id}>
                        <td>{runs.length - i}</td>
                        <td className="stats-table__cid">{r.campaign_id}</td>
                        <td>
                          <span
                            className="stats-ending-badge"
                            style={{
                              background: ENDING_COLOR[r.ending] || '#a89b82',
                              color: '#fff',
                            }}
                          >
                            {r.ending}
                          </span>
                        </td>
                        <td>{r.final_turn}</td>
                        <td>{r.final_score}</td>
                        <td style={{ color: 'var(--color-text-muted)' }}>{(r.ended_at || '').slice(0, 16)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '14px' }}>
          <button type="button" className="btn btn--primary" onClick={onClose}>关闭</button>
        </div>
      </div>
    </div>
  )
}
