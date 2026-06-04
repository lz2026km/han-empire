/* =============================================
   Header - Top status bar
   v2.1.0 Phase 3.3: 加主题切换 + 季节指示按钮
   v5.2.0 P6-4: 加 4 入口按钮 (主菜单/国势/设置/帮助)
   v5.5.0+ P8-G8: 5 阶品秩图 (rank/rank_*_formal.jpg)
   ============================================= */
import { Menu, BarChart3, Settings, HelpCircle } from 'lucide-react'
import type { GameState } from '../types'

interface Props {
  gameState: GameState | null
  onSave?: () => void
  onNewGame?: () => void
  onReturnToMenu?: () => void
  onOpenStateModal?: () => void
  onOpenSettingsModal?: () => void
  onOpenHelpModal?: () => void
  theme?: 'light' | 'dark'
  season?: 'spring' | 'summer' | 'autumn' | 'winter'
  onToggleTheme?: () => void
  onCycleSeason?: () => void
}

// v5.5.0+ P8-G8: 5 阶品秩 (rank/rank_*_formal.jpg)
const RANK_IMG: Record<string, string> = {
  gong: '/rank/rank_gong_formal.jpg',
  hou: '/rank/rank_hou_formal.jpg',
  bo: '/rank/rank_bo_formal.jpg',
  zi: '/rank/rank_zi_formal.jpg',
  nan: '/rank/rank_nan_formal.jpg',
}

const SEASON_LABEL: Record<string, string> = {
  spring: '春',
  summer: '夏',
  autumn: '秋',
  winter: '冬',
}

export function Header({ gameState, onSave, onNewGame, onReturnToMenu, onOpenStateModal, onOpenSettingsModal, onOpenHelpModal, theme, season, onToggleTheme, onCycleSeason }: Props) {
  return (
    <header className="app-header">
      <h1 className="app-header__title">
        <img src={RANK_IMG.gong} alt="" className="rank-icon" style={{ width: 24, height: 24, marginRight: 6 }} />
        汉献帝之末路
      </h1>

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
        <button type="button" className="btn" onClick={onReturnToMenu || onNewGame} data-tooltip="主菜单 (Esc)">
          <Menu size={14} /> 主菜单
        </button>
        {gameState && onOpenStateModal && (
          <button type="button" className="btn" onClick={onOpenStateModal} data-tooltip="国势详情 (S)">
            <BarChart3 size={14} /> 国势
          </button>
        )}
        {onOpenSettingsModal && (
          <button type="button" className="btn" onClick={onOpenSettingsModal} data-tooltip="设置">
            <Settings size={14} /> 设置
          </button>
        )}
        {onOpenHelpModal && (
          <button type="button" className="btn" onClick={onOpenHelpModal} data-tooltip="帮助 (?)">
            <HelpCircle size={14} /> 帮助
          </button>
        )}
        {gameState && (
          <button type="button" className="btn btn--gold" onClick={onSave}>存储 存档</button>
        )}
      </div>
    </header>
  )
}
