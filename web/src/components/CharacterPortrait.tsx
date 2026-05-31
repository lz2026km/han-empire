import { useState } from 'react'
import './CharacterPortrait.css'

interface CharacterPortraitProps {
  name: string
  faction?: string
  position?: string
  loyalty?: number
  ability?: number
  command?: number
  courage?: number
  portraitId?: string
  size?: 'small' | 'medium' | 'large'
  showStats?: boolean
  onClick?: () => void
  selected?: boolean
  portraitMode?: boolean
}

const FACTION_COLORS: Record<string, string> = {
  '汉室': '#4a2c2c', '曹魏': '#2c4a4a', '蜀汉': '#2D5A27',
  '东吴': '#5C4033', '袁氏': '#4a235a', '吕布': '#8B4513',
  '公孙瓒': '#2c4a6a', '董卓': '#5a2c2c', '凉州集团': '#6b4513', '中立': '#4a4a4a',
}

const getStatColor = (v: number) => v >= 80 ? '#22c55e' : v >= 60 ? '#84cc16' : v >= 40 ? '#eab308' : v >= 20 ? '#f97316' : '#ef4444'

export function CharacterPortrait({
  name,
  faction = '中立',
  position = '',
  loyalty = 50,
  ability = 50,
  command = 50,
  courage = 50,
  portraitId,
  size = 'medium',
  showStats = true,
  onClick,
  selected = false,
  portraitMode = false
}: CharacterPortraitProps) {
  const [imgError, setImgError] = useState(false)
  const sizeClass = `portrait--${size}`
  const factionColor = FACTION_COLORS[faction] || FACTION_COLORS['中立']

  return (
    <div 
      className={`
        character-portrait 
        ${sizeClass} 
        ${selected ? 'cp--selected' : ''} 
        ${onClick ? 'cp--clickable' : ''}
        ${portraitMode ? 'portrait-mode' : ''}
      `} 
      onClick={onClick}
      style={{ '--faction-color': factionColor } as React.CSSProperties}
    >
      <div className="cp__frame">
        <div className="cp__ink-border"></div>
        <div className="cp__gold-trim"></div>
        <div className="cp__portrait-bg"></div>
        <div className="cp__inner-frame"></div>
        {portraitId && !imgError ? (
          <img 
            src={`/portraits/${portraitId}.png`} 
            alt={name} 
            className="cp__image" 
            onError={() => setImgError(true)} 
          />
        ) : (
          <div className="cp__initials">{name.charAt(0)}</div>
        )}
        {selected && <div className="cp__selected-ring"></div>}
      </div>
      
      {showStats && (
        <div className="cp__info">
          <div className="cp__name">{name}</div>
          {position && <div className="cp__office">{position}</div>}
          <div className="cp__faction-badge" style={{ borderColor: factionColor }}>
            {faction}
          </div>
          
          <div className="cp__stats">
            <div className="cp__stat-bar">
              <span className="cp__stat-label">忠</span>
              <div className="cp__stat-track">
                <div 
                  className="cp__stat-fill cp__stat-fill--loyalty" 
                  style={{ width: `${loyalty}%` }} 
                />
              </div>
              <span className="cp__stat-value">{loyalty}</span>
            </div>
            
            <div className="cp__stat-bar">
              <span className="cp__stat-label">能</span>
              <div className="cp__stat-track">
                <div 
                  className="cp__stat-fill cp__stat-fill--ability" 
                  style={{ width: `${ability}%`, background: `linear-gradient(90deg, ${getStatColor(ability)}88, ${getStatColor(ability)})` }} 
                />
              </div>
              <span className="cp__stat-value">{ability}</span>
            </div>
            
            <div className="cp__stat-bar">
              <span className="cp__stat-label">统</span>
              <div className="cp__stat-track">
                <div 
                  className="cp__stat-fill cp__stat-fill--command" 
                  style={{ width: `${command}%` }} 
                />
              </div>
              <span className="cp__stat-value">{command}</span>
            </div>
            
            <div className="cp__stat-bar">
              <span className="cp__stat-label">勇</span>
              <div className="cp__stat-track">
                <div 
                  className="cp__stat-fill cp__stat-fill--courage" 
                  style={{ width: `${courage}%` }} 
                />
              </div>
              <span className="cp__stat-value">{courage}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}