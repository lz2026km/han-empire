// v2.0.0 Phase 3.1: 舆图 Tab - 抽自 App.tsx:862-895 (34 行)
// "三国专家"视角：东汉十三州核心 8 州
import { useState } from 'react'
import { ProvinceMap } from '../ProvinceMap'

// v2.0.0 Phase 3.1 TODO: 改用真 API 取代 mock 数据
// 现状：mock 8 州（汉末 13 州 + 朝迁 4 次的核心 8 个）
const MOCK_REGIONS = [
  { id: 'luoyang', name: '洛阳', kind: 'capital', unrest: 45, public_support: 60, controlled_by: 'caowei', status: 'controlled' },
  { id: 'chang_an', name: '长安', kind: 'capital', unrest: 70, public_support: 40, controlled_by: 'liubei', status: 'controlled' },
  { id: 'yuzhou', name: '豫州', kind: 'province', unrest: 30, public_support: 70, controlled_by: 'caowei', status: 'controlled' },
  { id: 'yanzhou', name: '兖州', kind: 'province', unrest: 55, public_support: 50, controlled_by: 'caowei', status: 'controlled' },
  { id: 'jingzhou', name: '荆州', kind: 'province', unrest: 40, public_support: 65, controlled_by: 'sunquan', status: 'allied' },
  { id: 'yangzhou', name: '扬州', kind: 'province', unrest: 25, public_support: 75, controlled_by: 'sunquan', status: 'allied' },
  { id: 'xuzhou', name: '徐州', kind: 'province', unrest: 60, public_support: 45, controlled_by: 'caowei', status: 'controlled' },
  { id: 'yizhou', name: '益州', kind: 'province', unrest: 35, public_support: 68, controlled_by: 'liubei', status: 'allied' },
]

export function MapTab() {
  const [selectedRegion, setSelectedRegion] = useState<any>(null)

  return (
    <div className="fade-in">
      <ProvinceMap
        regions={MOCK_REGIONS}
        onProvinceClick={(region) => setSelectedRegion(region)}
        selectedProvinceId={selectedRegion?.id}
      />
      {selectedRegion && (
        <div className="map-region-detail">
          <h4>{selectedRegion.name}</h4>
          <div className="region-detail-stats">
            <div>动荡程度: {selectedRegion.unrest}%</div>
            <div>民心: {selectedRegion.public_support}%</div>
            <div>控制势力: {selectedRegion.controlled_by}</div>
          </div>
        </div>
      )}
    </div>
  )
}
