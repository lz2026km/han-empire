import { useState } from 'react'
import './FactionRelationDiagram.css'

export interface FactionNode { id: string; name: string; influence: number; leader?: string; color: string }
export type RelationType = 'alliance' | 'neutral' | 'hostile' | 'dominated'
export interface FactionRelation { from: string; to: string; type: RelationType; strength?: number }

const REL_STYLES: Record<RelationType, { color: string; dash: string; w: number }> = {
  alliance: { color: '#22c55e', dash: '0', w: 3 },
  neutral: { color: '#6b7280', dash: '5,5', w: 2 },
  hostile: { color: '#ef4444', dash: '10,5', w: 3 },
  dominated: { color: '#f59e0b', dash: '3,3', w: 2 },
}

const FACTION_COLORS: Record<string, string> = {
  '忠汉派': '#8b2a2a', '务实派': '#2a4a4a', '离心派': '#4a2a4a', '叛逆派': '#5a1a1a',
  '汉室': '#4a2c2c', '曹魏': '#1e3a5f', '蜀汉': '#2D5A27', '东吴': '#5C4033',
}

export function FactionRelationDiagram({ factions, relations, onFactionClick, selectedFactionId }: { factions: FactionNode[]; relations: FactionRelation[]; onFactionClick?: (id: string) => void; selectedFactionId?: string }) {
  const [hovered, setHovered] = useState<string | null>(null)

  const pos = factions.reduce((acc, f, i) => {
    const a = (2 * Math.PI * i) / factions.length
    acc[f.id] = { x: 250 + 180 * Math.cos(a), y: 200 + 180 * Math.sin(a) }
    return acc
  }, {} as Record<string, { x: number; y: number }>)

  const getFiltRel = () => {
    const af = hovered || selectedFactionId
    if (!af) return relations
    return relations.filter(r => r.from === af || r.to === af)
  }

  return (
    <div className="faction-diagram">
      <svg viewBox="0 0 500 400" className="diagram-svg">
        <defs>
          <filter id="glow"><feGaussianBlur stdDeviation="3" result="cb"/><feMerge><feMergeNode in="cb"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
          <marker id="ah" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0,10 3.5,0 7" fill="#22c55e"/></marker>
          <marker id="hh" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0,10 3.5,0 7" fill="#ef4444"/></marker>
        </defs>
        {getFiltRel().map((rel, i) => {
          const f = pos[rel.from]
          const t = pos[rel.to]
          if (!f || !t) return null
          const s = REL_STYLES[rel.type]
          return (
            <line key={i} x1={f.x} y1={f.y} x2={t.x} y2={t.y} stroke={s.color} strokeWidth={s.w} strokeDasharray={s.dash}
              className={`relation-stroke ${rel.type}`} markerEnd={rel.type === 'alliance' || rel.type === 'hostile' ? `url(#${rel.type === 'alliance' ? 'ah' : 'hh'})` : undefined} />
          )
        })}
        {factions.map(f => {
          const p = pos[f.id]
          if (!p) return null
          const sz = 60 + (f.influence / 100) * 40
          const sel = selectedFactionId === f.id
          const hov = hovered === f.id
          const col = f.color || FACTION_COLORS[f.id] || '#4a4a4a'
          return (
            <g key={f.id} className={`faction-node ${sel ? 'selected' : ''} ${hov ? 'hovered' : ''}`}
              onClick={() => onFactionClick?.(f.id)} onMouseEnter={() => setHovered(f.id)} onMouseLeave={() => setHovered(null)} style={{ cursor: 'pointer' }}>
              {(sel || hov) && <circle cx={p.x} cy={p.y} r={sz / 2 + 10} fill={col} opacity={0.3} filter="url(#glow)" />}
              <circle cx={p.x} cy={p.y} r={sz / 2} fill={col} stroke={sel ? '#FFD700' : '#2D3748'} strokeWidth={sel ? 4 : 2} className="faction-circle" />
              <text x={p.x} y={p.y - sz / 2 - 15} textAnchor="middle" className="faction-name" fill="#e8dcc8" fontSize="13" fontWeight="600">{f.name}</text>
              <rect x={p.x - 25} y={p.y + sz / 2 + 8} width={50} height={6} rx={3} fill="#1a1a22" />
              <rect x={p.x - 25} y={p.y + sz / 2 + 8} width={50 * (f.influence / 100)} height={6} rx={3} fill={col} className="influence-fill" />
              <text x={p.x} y={p.y + sz / 2 + 24} textAnchor="middle" className="influence-text" fill="#c9a84c" fontSize="11">{f.influence}</text>
            </g>
          )
        })}
      </svg>
      <div className="diagram-legend">
        <div className="legend-title">派系关系</div>
        {Object.entries(REL_STYLES).map(([t, s]) => (
          <div key={t} className="legend-item">
            <svg width="30" height="12"><line x1="0" y1="6" x2="30" y2="6" stroke={s.color} strokeWidth={s.w} strokeDasharray={s.dash} /></svg>
            <span>{t === 'alliance' ? '同盟' : t === 'neutral' ? '中立' : t === 'hostile' ? '敌对' : '从属'}</span>
          </div>
        ))}
      </div>
      {(selectedFactionId || hovered) && (() => {
        const f = factions.find(f => f.id === (selectedFactionId || hovered))
        if (!f) return null
        return (
          <div className="faction-info-panel fade-in">
            <div className="info-header" style={{ borderLeftColor: f.color || FACTION_COLORS[f.id] || '#c9a84c' }}>
              <h3>{f.name}</h3>
              {f.leader && <p className="leader">领袖: {f.leader}</p>}
            </div>
            <div className="info-stats">
              <div className="stat-row"><span>影响力</span><span>{f.influence}</span></div>
            </div>
          </div>
        )
      })()}
    </div>
  )
}