import { useState, useEffect } from 'react'
import { X, ZoomIn, ZoomOut, MapPin, AlertTriangle } from 'lucide-react'

interface Province {
  id: string
  name: string
  path: string
  controller: 'emperor' | 'warlord' | 'rebel' | 'none'
  controllerName?: string
  troops: number
  population: number
  taxRate: number
  loyalty: number
}

interface GrandMapProps {
  isOpen: boolean
  onClose: () => void
  provinces: Province[]
  onProvinceClick?: (provinceId: string) => void
}

export function GrandMap({ isOpen, onClose, provinces, onProvinceClick }: GrandMapProps) {
  const [selectedProvince, setSelectedProvince] = useState<Province | null>(null)
  const [zoom, setZoom] = useState(1)
  const [filter, setFilter] = useState<'all' | 'emperor' | 'warlord' | 'rebel'>('all')

  // W2: Escape 关闭支持 (v3.3 UX 大修)
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  // W2: 打开时焦点陷阱 — 锁定 body 滚动
  useEffect(() => {
    if (isOpen) {
      const orig = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => { document.body.style.overflow = orig; };
    }
  }, [isOpen]);

  const filteredProvinces = filter === 'all'
    ? provinces
    : provinces.filter(p => p.controller === filter)

  const getControllerColor = (controller: Province['controller']) => {
    switch (controller) {
      case 'emperor': return '#d4af37'
      case 'warlord': return '#8b4513'
      case 'rebel': return '#8b0000'
      case 'none': return '#666666'
      default: return '#666666'
    }
  }

  const handleProvinceClick = (province: Province) => {
    setSelectedProvince(province)
    onProvinceClick?.(province.id)
  }

  const totalPopulation = provinces.reduce((sum, p) => sum + p.population, 0)
  const totalTroops = provinces.reduce((sum, p) => sum + p.troops, 0)

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="grand-map" onClick={e => e.stopPropagation()}>
        <div className="grand-map__header">
          <h2 className="grand-map__title">
            <MapPin size={20} />
            汉室疆域
          </h2>
          <div className="grand-map__controls">
            <button type="button"
              className="btn grand-map__zoom"
              onClick={() => setZoom(z => Math.min(z + 0.2, 2))}
              disabled={zoom >= 2}
            >
              <ZoomIn size={16} />
            </button>
            <button type="button"
              className="btn grand-map__zoom"
              onClick={() => setZoom(z => Math.max(z - 0.2, 0.5))}
              disabled={zoom <= 0.5}
            >
              <ZoomOut size={16} />
            </button>
            <select
              className="grand-map__filter"
              value={filter}
              onChange={e => setFilter(e.target.value as typeof filter)}
            >
              <option value="all">全部势力</option>
              <option value="emperor">皇室直辖</option>
              <option value="warlord">诸侯割据</option>
              <option value="rebel">叛军</option>
            </select>
          </div>
          <button type="button" className="grand-map__close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="grand-map__stats">
          <div className="grand-map__stat">
            <span className="grand-map__stat-label">总人口</span>
            <span className="grand-map__stat-value">{totalPopulation.toLocaleString()}</span>
          </div>
          <div className="grand-map__stat">
            <span className="grand-map__stat-label">总兵力</span>
            <span className="grand-map__stat-value">{totalTroops.toLocaleString()}</span>
          </div>
          <div className="grand-map__stat">
            <span className="grand-map__stat-label">州郡数</span>
            <span className="grand-map__stat-value">{provinces.length}</span>
          </div>
        </div>

        <div className="grand-map__container">
          <svg
            className="grand-map__svg"
            viewBox="0 0 800 600"
            style={{ transform: `scale(${zoom})` }}
          >
            <defs>
              <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#333" strokeWidth="0.5" />
              </pattern>
            </defs>
            <rect width="800" height="600" fill="url(#grid)" />

            {filteredProvinces.map(province => (
              <g
                key={province.id}
                className="grand-map__province"
                onClick={() => handleProvinceClick(province)}
                style={{ cursor: 'pointer' }}
              >
                <path
                  d={province.path}
                  fill={getControllerColor(province.controller)}
                  fillOpacity={0.6}
                  stroke={selectedProvince?.id === province.id ? '#fff' : '#333'}
                  strokeWidth={selectedProvince?.id === province.id ? 3 : 1}
                />
                <text
                  x={province.path.split(' ')[0].match(/M(\d+)/)?.[1] || '0'}
                  y={province.path.split(' ')[1].match(/(\d+)/)?.[1] || '0'}
                  fill="#fff"
                  fontSize="10"
                  fontFamily="var(--font-serif)"
                  style={{ pointerEvents: 'none' }}
                >
                  {province.name}
                </text>
              </g>
            ))}
          </svg>

          {selectedProvince && (
            <div className="grand-map__tooltip">
              <div className="grand-map__tooltip-header">
                <span>{selectedProvince.name}</span>
                <span
                  className="grand-map__tooltip-controller"
                  style={{ background: getControllerColor(selectedProvince.controller) }}
                >
                  {selectedProvince.controllerName || selectedProvince.controller}
                </span>
              </div>
              <div className="grand-map__tooltip-stats">
                <div>兵力: {selectedProvince.troops.toLocaleString()}</div>
                <div>人口: {selectedProvince.population.toLocaleString()}</div>
                <div>税率: {selectedProvince.taxRate}%</div>
                {selectedProvince.loyalty >= 0 && <div>忠诚: {selectedProvince.loyalty}</div>}
              </div>
            </div>
          )}
        </div>

        <div className="grand-map__legend">
          <div className="grand-map__legend-item">
            <span className="grand-map__legend-color" style={{ background: '#d4af37' }} />
            <span>皇室直辖</span>
          </div>
          <div className="grand-map__legend-item">
            <span className="grand-map__legend-color" style={{ background: '#8b4513' }} />
            <span>诸侯割据</span>
          </div>
          <div className="grand-map__legend-item">
            <span className="grand-map__legend-color" style={{ background: '#8b0000' }} />
            <span>叛军</span>
          </div>
          <div className="grand-map__legend-item">
            <span className="grand-map__legend-color" style={{ background: '#666666' }} />
            <span>无主之地</span>
          </div>
        </div>
      </div>
    </div>
  )
}