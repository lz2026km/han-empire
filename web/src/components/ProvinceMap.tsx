import { useState } from 'react'
import { MapLegend } from './MapLegend'

export interface RegionData {
  id: string
  name: string
  kind: string
  unrest: number
  public_support: number
  controlled_by: string
  status: string
  population?: number
  tax_per_turn?: number
  grain_security?: number
}

export interface ProvinceMapProps {
  regions: RegionData[]
  onProvinceClick?: (region: RegionData) => void
  selectedProvinceId?: string
}

interface ProvincePath {
  id: string
  name: string
  path: string
  labelX: number
  labelY: number
}

const PROVINCE_PATHS: ProvincePath[] = [
  { id: 'luoyang', name: '洛阳', path: 'M320,180 L340,175 L355,185 L350,200 L330,205 L315,195 Z', labelX: 335, labelY: 190 },
  { id: 'chang_an', name: '长安', path: 'M280,210 L300,205 L310,220 L295,230 L275,225 Z', labelX: 290, labelY: 218 },
  { id: 'sanding', name: '三辅', path: 'M295,195 L315,190 L325,200 L315,215 L295,210 Z', labelX: 308, labelY: 203 },
  { id: 'hongnong', name: '弘农', path: 'M340,195 L360,190 L370,205 L355,215 L340,210 Z', labelX: 355, labelY: 203 },
  { id: 'yuzhou', name: '豫州', path: 'M380,160 L420,155 L430,175 L415,190 L385,185 L370,170 Z', labelX: 400, labelY: 172 },
  { id: 'yanzhou', name: '兖州', path: 'M380,125 L420,120 L430,140 L415,155 L385,150 L370,135 Z', labelX: 400, labelY: 138 },
  { id: 'jingzhou', name: '荆州', path: 'M420,220 L470,210 L485,240 L465,265 L420,260 L410,240 Z', labelX: 448, labelY: 238 },
  { id: 'yangzhou', name: '扬州', path: 'M480,150 L540,140 L555,170 L530,195 L485,185 L470,160 Z', labelX: 512, labelY: 168 },
  { id: 'xuzhou', name: '徐州', path: 'M440,100 L490,95 L505,120 L485,140 L445,135 L430,115 Z', labelX: 468, labelY: 118 },
  { id: 'qingzhou', name: '青州', path: 'M440,60 L490,55 L505,80 L485,100 L445,95 L430,75 Z', labelX: 468, labelY: 78 },
  { id: 'jizhou', name: '冀州', path: 'M350,80 L400,75 L415,100 L395,120 L350,115 L335,95 Z', labelX: 375, labelY: 98 },
  { id: 'youzhou', name: '幽州', path: 'M380,20 L440,15 L455,50 L425,75 L380,70 L365,45 Z', labelX: 410, labelY: 45 },
  { id: 'bingzhou', name: '并州', path: 'M290,60 L340,55 L355,80 L335,100 L290,95 L275,70 Z', labelX: 315, labelY: 78 },
  { id: 'liangzhou', name: '凉州', path: 'M200,180 L250,175 L265,210 L240,235 L195,230 L180,200 Z', labelX: 225, labelY: 205 },
  { id: 'yizhou', name: '益州', path: 'M260,260 L310,255 L325,300 L295,330 L255,325 L245,285 Z', labelX: 285, labelY: 292 },
  { id: 'jiaozhou', name: '交州', path: 'M430,340 L490,335 L505,380 L470,405 L425,400 L415,360 Z', labelX: 460, labelY: 370 },
]

const getUnrestColor = (unrest: number): string => {
  if (unrest >= 80) return '#8B0000'
  if (unrest >= 60) return '#CD5C5C'
  if (unrest >= 40) return '#DAA520'
  if (unrest >= 20) return '#6B8E23'
  return '#228B22'
}

const getStatusColor = (status: string, controlledBy: string): string => {
  if (status === 'ming') return '#4A5568'
  if (controlledBy === 'caowei' || controlledBy === 'caocao') return '#1E3A5F'
  if (controlledBy === 'liubei') return '#2D5A27'
  if (controlledBy === 'sunquan') return '#5C4033'
  if (controlledBy === 'yuanshao') return '#4A235A'
  if (controlledBy === 'lvbu') return '#8B4513'
  return '#6B7280'
}

export function ProvinceMap({ regions, onProvinceClick, selectedProvinceId }: ProvinceMapProps) {
  const [colorMode, setColorMode] = useState<'unrest' | 'control'>('unrest')

  const getRegionById = (id: string) => regions.find(r => r.id === id)

  const getFillColor = (provinceId: string): string => {
    const region = getRegionById(provinceId)
    if (!region) return '#9CA3AF'
    
    if (colorMode === 'unrest') {
      return getUnrestColor(region.unrest)
    }
    return getStatusColor(region.status, region.controlled_by)
  }

  const handleProvinceClick = (province: ProvincePath) => {
    const region = getRegionById(province.id)
    if (region && onProvinceClick) {
      onProvinceClick(region)
    }
  }

  return (
    <div className="province-map">
      <div className="map-header">
        <h3>汉朝疆域图</h3>
        <div className="color-mode-toggle">
          <button type="button" 
            className={colorMode === 'unrest' ? 'active' : ''}
            onClick={() => setColorMode('unrest')}
          >
            动荡程度
          </button>
          <button type="button" 
            className={colorMode === 'control' ? 'active' : ''}
            onClick={() => setColorMode('control')}
          >
            势力归属
          </button>
        </div>
      </div>

      <svg viewBox="0 0 600 450" className="map-svg">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {PROVINCE_PATHS.map(province => {
          const region = getRegionById(province.id)
          const isSelected = selectedProvinceId === province.id
          const isClickable = !!region

          return (
            <g key={province.id} className="province-group">
              <path
                d={province.path}
                fill={getFillColor(province.id)}
                stroke={isSelected ? '#FFD700' : '#2D3748'}
                strokeWidth={isSelected ? 3 : 1.5}
                className={`province-path ${isClickable ? 'clickable' : ''}`}
                onClick={() => handleProvinceClick(province)}
                filter={isSelected ? 'url(#glow)' : undefined}
              />
              <text
                x={province.labelX}
                y={province.labelY}
                className="province-label"
                textAnchor="middle"
                dominantBaseline="middle"
              >
                {province.name}
              </text>
              {region && (
                <text
                  x={province.labelX}
                  y={province.labelY + 12}
                  className="province-unrest"
                  textAnchor="middle"
                >
                  {region.unrest}%
                </text>
              )}
            </g>
          )
        })}

        <rect x="0" y="0" width="600" height="450" fill="none" stroke="#1A202C" strokeWidth="2" />
      </svg>

      <MapLegend colorMode={colorMode} />
    </div>
  )
}