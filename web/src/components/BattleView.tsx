import { useState, useEffect, useCallback } from 'react'
import './BattleView.css'

export interface BattleUnit { id: string; name: string; faction: string; troops: number; morale: number; strength: number; position: 'left' | 'right' }
export interface BattleResult { attacker: BattleUnit; defender: BattleUnit; rounds: BattleRound[]; winner: 'attacker' | 'defender' | 'draw'; casualties: { attacker: number; defender: number } }
export interface BattleRound { round: number; attackerRoll: number; defenderRoll: number; attackerDamage: number; defenderDamage: number; narrative: string }

export function BattleView({ attacker, defender, onBattleEnd, autoPlay = false }: { attacker: BattleUnit; defender: BattleUnit; onBattleEnd?: (r: BattleResult) => void; autoPlay?: boolean }) {
  const [round, setRound] = useState(0)
  const [playing, setPlaying] = useState(autoPlay)
  const [rounds, setRounds] = useState<BattleRound[]>([])
  const [ended, setEnded] = useState(false)
  const [winner, setWinner] = useState<'attacker' | 'defender' | 'draw' | null>(null)

  const simRound = useCallback((r: number, att: BattleUnit, def: BattleUnit): BattleRound => {
    const ar = Math.floor(Math.random() * 20) + 1 + Math.floor(att.morale / 20) + Math.floor(att.strength / 30)
    const dr = Math.floor(Math.random() * 20) + 1 + Math.floor(def.morale / 20) + Math.floor(def.strength / 30)
    const ad = ar > dr ? Math.floor(Math.random() * 20) + 5 : 0
    const dd = dr > ar ? Math.floor(Math.random() * 20) + 5 : 0
    return { round: r, attackerRoll: ar, defenderRoll: dr, attackerDamage: ad, defenderDamage: dd, narrative: ar > dr ? '攻势凶猛，敌军折损不少人马。' : dr > ar ? '敌军防守严密，我军攻势受阻。' : '双方僵持，胜负难分。' }
  }, [])

  useEffect(() => {
    if (!playing || ended) return
    const t = setTimeout(() => {
      const attTroops = Math.max(0, attacker.troops - rounds.reduce((s, r) => s + r.defenderDamage, 0))
      const defTroops = Math.max(0, defender.troops - rounds.reduce((s, r) => s + r.attackerDamage, 0))
      if (attTroops <= 0 || defTroops <= 0 || round >= 10) {
        let w: 'attacker' | 'defender' | 'draw' = 'draw'
        if (attTroops > defTroops) w = 'attacker'
        else if (defTroops > attTroops) w = 'defender'
        setWinner(w); setEnded(true); setPlaying(false)
        onBattleEnd?.({ attacker, defender, rounds, winner: w, casualties: { attacker: attacker.troops - attTroops, defender: defender.troops - defTroops } })
        return
      }
      setRounds(prev => [...prev, simRound(round + 1, attacker, defender)])
      setRound(prev => prev + 1)
    }, 1500)
    return () => clearTimeout(t)
  }, [playing, round, ended, attacker, defender, onBattleEnd, rounds, simRound])

  const start = () => { setRounds([]); setRound(0); setEnded(false); setWinner(null); setPlaying(true) }

  return (
    <div className="battle-view">
      <div className="battle-header">
        <h2 className="battle-title">⚔️ 战场态势</h2>
        <div className="battle-controls">
          {!ended && !playing && <button className="btn btn--primary" onClick={start}>⚔️ 开始战斗</button>}
          {playing && <button className="btn" onClick={() => setPlaying(false)}>⏸️ 暂停</button>}
          {!playing && round > 0 && !ended && <button className="btn" onClick={() => setPlaying(true)}>▶️ 继续</button>}
        </div>
      </div>
      <div className="battle-field">
        <div className="army-group army-group--attacker slide-in-left">
          <div className="army-info"><span className="army-name">{attacker.name}</span><span className="army-faction">{attacker.faction}</span></div>
          <div className="army-troops">
            <div className="troops-bar"><div className="troops-fill" style={{ width: `${Math.max(0, (attacker.troops - rounds.reduce((s, r) => s + r.defenderDamage, 0)) / attacker.troops * 100)}%` }} /></div>
            <span className="troops-count">{Math.max(0, attacker.troops - rounds.reduce((s, r) => s + r.defenderDamage, 0))} 兵</span>
          </div>
          <div className="army-stats"><span>士气: {attacker.morale}</span><span>战力: {attacker.strength}</span></div>
        </div>
        <div className="battle-center">
          {round > 0 && <div className="battle-round-indicator"><span className="round-label">第 {round} 回合</span></div>}
          <div className="vs-badge">VS</div>
          {ended && winner && <div className={`battle-result-banner ${winner === 'attacker' ? 'banner-unfurl' : 'critical-alert'}`}>{winner === 'attacker' ? '我军大胜！' : winner === 'defender' ? '敌军获胜...' : '战平'}</div>}
        </div>
        <div className="army-group army-group--defender slide-in-right">
          <div className="army-info"><span className="army-name">{defender.name}</span><span className="army-faction">{defender.faction}</span></div>
          <div className="army-troops">
            <div className="troops-bar"><div className="troops-fill troops-fill--defender" style={{ width: `${Math.max(0, (defender.troops - rounds.reduce((s, r) => s + r.attackerDamage, 0)) / defender.troops * 100)}%` }} /></div>
            <span className="troops-count">{Math.max(0, defender.troops - rounds.reduce((s, r) => s + r.attackerDamage, 0))} 兵</span>
          </div>
          <div className="army-stats"><span>士气: {defender.morale}</span><span>战力: {defender.strength}</span></div>
        </div>
      </div>
      {rounds.length > 0 && (
        <div className="battle-log">
          <h3>战斗经过</h3>
          <div className="log-entries">
            {rounds.map((r, i) => (
              <div key={r.round} className={`log-entry ${i === rounds.length - 1 ? 'log-entry--latest' : ''}`}>
                <div className="log-round">第{r.round}回合</div>
                <div className="log-dice"><span className="dice-roll">🎲 {r.attackerRoll}</span><span className="dice-vs">vs</span><span className="dice-roll">🎲 {r.defenderRoll}</span></div>
                <div className="log-damage">
                  {r.attackerDamage > 0 && <span className="damage-defender">守方伤亡: {r.attackerDamage}</span>}
                  {r.defenderDamage > 0 && <span className="damage-attacker">攻方伤亡: {r.defenderDamage}</span>}
                </div>
                <div className="log-narrative">{r.narrative}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}