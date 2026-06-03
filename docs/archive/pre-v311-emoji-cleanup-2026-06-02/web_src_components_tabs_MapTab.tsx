// v2.0.0 Phase 5.2: 舆图 Tab - 改用真 API 取代 mock 数据
// 51 州郡从 /api/regions 实时拉取
import { useState, useEffect } from 'react'
import { ProvinceMap } from '../ProvinceMap'
import { api } from '../../api'

// 真数据加载 (从 /api/regions 拉 51 州郡)
export function MapTab() {
  const [regions, setRegions] = useState<any[]>([])
  const [selectedRegion, setSelectedRegion] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    api.getRegions()
      .then((data) => {
        if (cancelled) return
        // 转 ProvinceMap 期望的 RegionData 格式
        const mapped = data.regions.map((r: any) => ({
          id: r.id,
          name: r.name,
          kind: r.kind || 'province',
          unrest: r.unrest ?? 50,
          public_support: r.public_support ?? 50,
          controlled_by: r.controlled_by || 'neutral',
          status: r.status || 'controlled',
          population: r.population,
          tax_per_turn: r.tax_per_turn,
          grain_security: r.grain_security,
        }))
        setRegions(mapped)
        setLoading(false)
      })
      .catch((e) => {
        if (cancelled) return
        setError(e.message || '加载州郡失败')
        setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return (
      <div className="fade-in map-loading">
        <p>⏳ 正在加载东汉十三州 51 州郡...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="fade-in map-error">
        <p>❌ 加载失败: {error}</p>
        <button onClick={() => window.location.reload()}>重试</button>
      </div>
    )
  }

  return (
    <div className="fade-in">
      <div className="map-header">
        <p>东汉十三州 · 共 {regions.length} 州郡 · 数据来源: regions.json</p>
      </div>
      <ProvinceMap
        regions={regions}
        onProvinceClick={(region) => setSelectedRegion(region)}
        selectedProvinceId={selectedRegion?.id}
      />
      {selectedRegion && (
        <div className="map-region-detail">
          <h4>{selectedRegion.name} · {selectedRegion.kind === 'capital' ? '都城' : '州郡'}</h4>
          <div className="region-detail-stats">
            <div>动荡程度: {selectedRegion.unrest}%</div>
            <div>民心: {selectedRegion.public_support}%</div>
            <div>控制势力: {selectedRegion.controlled_by}</div>
            {selectedRegion.population != null && (
              <div>人口: {selectedRegion.population} 万</div>
            )}
            {selectedRegion.tax_per_turn != null && (
              <div>每回合税收: {selectedRegion.tax_per_turn} 万两</div>
            )}
            {selectedRegion.grain_security != null && (
              <div>粮食安全: {selectedRegion.grain_security}%</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
