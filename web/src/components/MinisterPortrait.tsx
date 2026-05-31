import { useState } from 'react'
import './MinisterPortrait.css'

interface MinisterPortraitProps {
  name: string
  faction?: string
  loyalty?: number
  ability?: number
  portraitId?: string
  size?: 'small' | 'medium' | 'large'
  showStats?: boolean
  onClick?: () => void
  selected?: boolean
}

const FACTION_COLORS: Record<string, string> = {
  '汉室': '#4a2c2c', '曹魏': '#2c4a4a', '蜀汉': '#2D5A27',
  '东吴': '#5C4033', '袁氏': '#4a235a', '吕布': '#8B4513',
  '公孙瓒': '#2c4a6a', '董卓': '#5a2c2c', '凉州集团': '#6b4513', '中立': '#4a4a4a',
}

export function MinisterPortrait({ name, faction = '中立', loyalty = 50, ability = 50, portraitId, size = 'medium', showStats = true, onClick, selected = false }: MinisterPortraitProps) {
  const [imgError, setImgError] = useState(false)
  const sizeClass = `portrait--${size}`
  const factionColor = FACTION_COLORS[faction] || FACTION_COLORS['中立']
  const getStatColor = (v: number) => v >= 80 ? '#22c55e' : v >= 60 ? '#84cc16' : v >= 40 ? '#eab308' : v >= 20 ? '#f97316' : '#ef4444'

  return (
    <div className={`minister-portrait ${sizeClass} ${selected ? 'portrait--selected' : ''} ${onClick ? 'portrait--clickable' : ''}`} onClick={onClick} style={{ '--faction-color': factionColor } as React.CSSProperties}>
      <div className="portrait__frame">
        <div className="portrait__border"></div>
        {portraitId && !imgError ? (
          <img src={`/portraits/${portraitId}.png`} alt={name} className="portrait__image" onError={() => setImgError(true)} />
        ) : (
          <div className="portrait__initials">{name.charAt(0)}</div>
        )}
        {selected && <div className="portrait__selected-ring"></div>}
      </div>
      {showStats && (
        <div className="portrait__stats">
          <div className="portrait__name">{name}</div>
          <div className="portrait__faction" style={{ backgroundColor: factionColor }}>{faction}</div>
          <div className="portrait__bars">
            <div className="stat-bar">
              <span className="stat-bar__label">忠</span>
              <div className="stat-bar__track"><div className="stat-bar__fill" style={{ width: `${loyalty}%`, backgroundColor: getStatColor(loyalty) }} /></div>
            </div>
            <div className="stat-bar">
              <span className="stat-bar__label">能</span>
              <div className="stat-bar__track"><div className="stat-bar__fill" style={{ width: `${ability}%`, backgroundColor: getStatColor(ability) }} /></div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}