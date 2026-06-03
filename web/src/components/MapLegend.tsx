import './MapLegend.css'

interface MapLegendProps {
  colorMode: 'unrest' | 'control'
}

export function MapLegend({ colorMode }: MapLegendProps) {
  if (colorMode === 'unrest') {
    return (
      <div className="map-legend">
        <h4>动荡程度图例</h4>
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#228B22' }} />
            <span className="legend-label">安定 (0-19%)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#6B8E23' }} />
            <span className="legend-label">平稳 (20-39%)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#DAA520' }} />
            <span className="legend-label">动荡 (40-59%)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#CD5C5C' }} />
            <span className="legend-label">混乱 (60-79%)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#8B0000' }} />
            <span className="legend-label">危机 (80-100%)</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="map-legend">
      <h4>势力归属图例</h4>
      <div className="legend-items">
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#4A5568' }} />
          <span className="legend-label">朝廷直辖</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#1E3A5F' }} />
          <span className="legend-label">曹操/曹魏</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#2D5A27' }} />
          <span className="legend-label">刘备/蜀汉</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#5C4033' }} />
          <span className="legend-label">孙权/东吴</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#4A235A' }} />
          <span className="legend-label">袁绍</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#8B4513' }} />
          <span className="legend-label">吕布</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#6B7280' }} />
          <span className="legend-label">其他势力</span>
        </div>
      </div>
    </div>
  )
}