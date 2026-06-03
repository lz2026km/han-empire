import type { GameState } from '../types'
import './EmperorPanel.css'

interface EmperorPanelProps {
  gameState: GameState | null
}

const LUNAR_MONTHS = ['正', '二', '三', '四', '五', '六', '七', '八', '九', '十', '冬', '腊']

export function EmperorPanel({ gameState }: EmperorPanelProps) {
  if (!gameState) return null

  const lunarMonth = LUNAR_MONTHS[gameState.month - 1] || '正'

  return (
    <div className="emperor-panel">
      <div className="emperor-panel__decorative" />
      
      <div className="emperor-panel__header">
        <span className="emperor-panel__title">帝王</span>
        <div className="emperor-panel__seal">玺</div>
      </div>

      <div className="emperor-panel__portrait">
        <div className="emperor-panel__portrait-frame">
          <div className="emperor-panel__portrait-ring" />
          <div className="emperor-panel__portrait-inner">
            {gameState.emperor_name?.charAt(0) || '汉'}
          </div>
        </div>
        <div className="emperor-panel__name">{gameState.emperor_name || '汉献帝'}</div>
        <div className="emperor-panel__era">建安年间</div>
      </div>

      <div className="emperor-panel__date">
        <div className="emperor-panel__date-item">
          <div className="emperor-panel__date-label">月</div>
          <div className="emperor-panel__date-value">{gameState.month}</div>
          <div className="emperor-panel__date-lunar">{lunarMonth}月</div>
        </div>
        <div className="emperor-panel__date-item">
          <div className="emperor-panel__date-label">年</div>
          <div className="emperor-panel__date-value">{gameState.year}</div>
          <div className="emperor-panel__date-lunar">中平元年</div>
        </div>
      </div>

      <div className="emperor-panel__metrics">
        <div className="emperor-panel__metric">
          <div className="emperor-panel__metric-header">
            <span className="emperor-panel__metric-label">
              <span className="emperor-panel__metric-icon">
                <span className="resource-icon-people" style={{ width: 24, height: 24, verticalAlign: 'middle' }} />
              </span>
              威权
            </span>
            <span className="emperor-panel__metric-value">
              {gameState.emperor_authority}/100
            </span>
          </div>
          <div className="emperor-panel__metric-track">
            <div 
              className="emperor-panel__metric-fill emperor-panel__metric-fill--authority"
              style={{ width: `${Math.min(gameState.emperor_authority, 100)}%` }}
            />
          </div>
        </div>

        <div className="emperor-panel__metric">
          <div className="emperor-panel__metric-header">
            <span className="emperor-panel__metric-label">
              <span className="emperor-panel__metric-icon">
                <span className="resource-icon-heart" style={{ width: 24, height: 24, verticalAlign: 'middle' }} />
              </span>
              声望
            </span>
            <span className="emperor-panel__metric-value">
              {gameState.emperor_loyalty}/100
            </span>
          </div>
          <div className="emperor-panel__metric-track">
            <div 
              className="emperor-panel__metric-fill emperor-panel__metric-fill--prestige"
              style={{ width: `${Math.min(gameState.emperor_loyalty, 100)}%` }}
            />
          </div>
        </div>

        <div className="emperor-panel__metric">
          <div className="emperor-panel__metric-header">
            <span className="emperor-panel__metric-label">
              <span className="emperor-panel__metric-icon">
                <span className="resource-icon-troops" style={{ width: 24, height: 24, verticalAlign: 'middle' }} />
              </span>
              藩镇
            </span>
            <span className="emperor-panel__metric-value">
              {Math.round((gameState.turn_count * 2.5) % 100)}/100
            </span>
          </div>
          <div className="emperor-panel__metric-track">
            <div 
              className="emperor-panel__metric-fill emperor-panel__metric-fill--warlords"
              style={{ width: `${Math.round((gameState.turn_count * 2.5) % 100)}%` }}
            />
          </div>
        </div>

        <div className="emperor-panel__metric">
          <div className="emperor-panel__metric-header">
            <span className="emperor-panel__metric-label">
              <span className="emperor-panel__metric-icon">
                <span className="resource-icon-gold" style={{ width: 24, height: 24, verticalAlign: 'middle' }} />
              </span>
              汉室库
            </span>
            <span className="emperor-panel__metric-value">
              {Math.round((gameState.turn_count * 8.5) % 10000)}两
            </span>
          </div>
          <div className="emperor-panel__metric-track">
            <div 
              className="emperor-panel__metric-fill emperor-panel__metric-fill--treasury"
              style={{ width: `${Math.min(Math.round((gameState.turn_count * 8.5) % 10000) / 100, 100)}%` }}
            />
          </div>
        </div>
      </div>

      <div className="emperor-panel__dragon" />
    </div>
  )
}