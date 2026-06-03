/* =============================================
   Header - Top status bar
   v2.1.0 Phase 3.3: 加主题切换 + 季节指示按钮
   ============================================= */
import type { GameState } from '../types'

interface Props {
  gameState: GameState | null
  onSave?: () => void
  onNewGame?: () => void
  // v5.2.0 P6-1: 游戏中按"新朝"返回主菜单
  onReturnToMenu?: () => void
  theme?: 'light' | 'dark'
  season?: 'spring' | 'summer' | 'autumn' | 'winter'
  onToggleTheme?: () => void
  onCycleSeason?: () => void
}

// v2.1.0 Phase 3.3: 季节中文名 + emoji
const SEASON_LABEL: Record<string, string> = {
  spring: '春',
  summer: '夏',
  autumn: '秋',
  winter: '冬',
}
const SEASON_ICON: Record<string, string> = {
  spring: '春',
  summer: '夏️',
  autumn: '秋',
  winter: '冬️',
}

export function Header({ gameState, onSave, onNewGame, onReturnToMenu, theme, season, onToggleTheme, onCycleSeason }: Props) {
  return (
    <header className="app-header">
      <h1 className="app-header__title">战斗️ 汉献帝之末路</h1>

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

      <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px', alignItems: 'center' }}>
        {/* v2.1.0 Phase 3.3: 季节指示器 + 切换按钮 */}
        {season && onCycleSeason && (
          <button type="button"
            className="btn btn--season"
            onClick={onCycleSeason}
            data-tooltip="点击切换季节"
            style={{ minWidth: '44px' }}
          >
            {SEASON_ICON[season]} {SEASON_LABEL[season]}
          </button>
        )}
        {/* v2.1.0 Phase 3.3: 主题切换按钮 */}
        {onToggleTheme && (
          <button type="button"
            className="btn btn--theme"
            onClick={onToggleTheme}
            data-tooltip={`切换${theme === 'dark' ? '亮色' : '暗色'}主题`}
            style={{ minWidth: '44px' }}
          >
            {theme === 'dark' ? '夏️' : '夜'}
          </button>
        )}
        <button type="button" className="btn" onClick={onReturnToMenu || onNewGame}>主菜单</button>
        {gameState && (
          <button type="button" className="btn btn--gold" onClick={onSave}>存储 存档</button>
        )}
      </div>
    </header>
  )
}
