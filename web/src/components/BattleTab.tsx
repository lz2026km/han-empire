/* =============================================
   BattleTab - 历史战役推演
   v2.1.0 Phase 4.3
   ============================================= */
import { useState, useEffect } from 'react'
import { api } from '../api'
import { BattleView, type BattleUnit, type BattleResult } from './BattleView'

interface HistoricalBattle {
  battle_id: string
  battle_name: string
  year: number
  location: string
  background: string
  sides: string[]
  troop_count: number
  total_troops: number
}

interface BattleReport {
  battle_id: string
  battle_name: string
  year: number
  location: string
  sides: string[]
  initial_troops: Record<string, number>
  rounds: Array<{
    round: number
    actions: string[]
    casualties: Record<string, number>
    weather: string
    narrative: string
  }>
  winner: string | null
  final_troops: Record<string, number>
  casualties_total: Record<string, number>
  loot: Record<string, number>
  summary: string
}

export function BattleTab() {
  const [battles, setBattles] = useState<HistoricalBattle[]>([])
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const [report, setReport] = useState<BattleReport | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.listBattles().then(r => setBattles(r.battles || []))
  }, [])

  const handleSimulate = async (key: string) => {
    setLoading(true)
    setSelectedKey(key)
    try {
      const r = await api.simulateBattle(key)
      setReport(r.report)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="battle-tab">
      <h2>战斗️ 历史战役推演</h2>
      <p className="battle-tab__desc">主公可推演东汉末年 3 大著名战役, 体验群雄逐鹿。</p>

      <div className="battle-list">
        {battles.map(b => (
          <div
            key={b.battle_id}
            className={`battle-card ${selectedKey === b.battle_id.split('_')[1] ? 'battle-card--active' : ''}`}
            onClick={() => handleSimulate(b.battle_id.split('_')[1])}
            data-tooltip={`点击推演 ${b.battle_name}`}
          >
            <div className="battle-card__year">{b.year}年</div>
            <div className="battle-card__name">{b.battle_name}</div>
            <div className="battle-card__location">针 {b.location}</div>
            <div className="battle-card__sides">
              {b.sides.map(s => <span key={s} className="faction-tag">{s}</span>)}
            </div>
            <div className="battle-card__troops">战斗️ {b.total_troops.toLocaleString()} 兵 · {b.troop_count} 部</div>
            <div className="battle-card__bg">{b.background}</div>
          </div>
        ))}
      </div>

      {loading && <div className="loading">推演中...</div>}

      {report && !loading && (
        <div className="battle-report">
          <h3>诏书 {report.battle_name} · {report.year}年</h3>
          <div className="battle-report__summary">{report.summary}</div>
          {report.winner && (
            <div className="battle-report__winner">成就 胜方: {report.winner}</div>
          )}

          <h4>战斗经过 (共 {report.rounds.length} 回合)</h4>
          {report.rounds.map((r, i) => (
            <div key={i} className={`battle-round ${i === report.rounds.length - 1 ? 'battle-round--latest' : ''}`}>
              <div className="battle-round__header">
                <span className="battle-round__num">第 {r.round} 回合</span>
                <span className="battle-round__weather">云 {r.weather}</span>
              </div>
              <div className="battle-round__narrative">{r.narrative}</div>
              {Object.keys(r.casualties).length > 0 && (
                <div className="battle-round__casualties">
                  伤亡: {Object.entries(r.casualties).map(([k, v]) => `${k}(${v})`).join(', ')}
                </div>
              )}
            </div>
          ))}

          {Object.keys(report.casualties_total).length > 0 && (
            <div className="battle-report__casualties-total">
              <h4>总伤亡</h4>
              {Object.entries(report.casualties_total).map(([k, v]) => (
                <div key={k}>{k}: {v} 人</div>
              ))}
            </div>
          )}

          {Object.keys(report.loot).length > 0 && (
            <div className="battle-report__loot">
              <h4>战利品</h4>
              {Object.entries(report.loot).map(([k, v]) => (
                <span key={k} className="loot-tag">{k}+{v}</span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
