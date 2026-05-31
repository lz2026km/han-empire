/* =============================================
   Header - Top status bar
   ============================================= */
import type { GameState } from '../types'

interface Props {
  gameState: GameState | null
  onSave?: () => void
  onNewGame?: () => void
}

export function Header({ gameState, onSave, onNewGame }: Props) {
  return (
    <header className="app-header">
      <h1 className="app-header__title">⚔️ 汉献帝之末路</h1>

      {gameState && (
        <>
          <span className="app-header__year">
            {gameState.year}年 · {gameState.month}月
          </span>

          <div className="app-header__stats">
            <div className="stat-badge">
              <span className="stat-badge__label">威权</span>
              <span className="stat-badge__value">{gameState.emperor_authority}</span>
            </div>
            <div className="stat-badge">
              <span className="stat-badge__label">忠诚</span>
              <span className="stat-badge__value">{gameState.emperor_loyalty}</span>
            </div>
            <div className="stat-badge">
              <span className="stat-badge__label">回合</span>
              <span className="stat-badge__value">{gameState.turn_count}</span>
            </div>
          </div>
        </>
      )}

      <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
        <button className="btn" onClick={onNewGame}>新朝</button>
        {gameState && (
          <button className="btn btn--gold" onClick={onSave}>💾 存档</button>
        )}
      </div>
    </header>
  )
}