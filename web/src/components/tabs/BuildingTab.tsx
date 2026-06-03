// v2.0.0 Phase 3.1: 抽自 App.tsx:778-844 (67 行)
// 汉风术语："营造"对应 buildings (汉代宫室营造需银两调度)
import { useState, useEffect } from 'react'
import { api } from '../../api'

interface BuildingTabProps {
  campaignId: string
}

interface BuildingsState {
  buildings: { id: string; name: string; level: number; effect_str: string; constructed: boolean; cost: number }[]
  total_slots: number
}

export function BuildingTab({ campaignId }: BuildingTabProps) {
  const [buildings, setBuildings] = useState<BuildingsState | null>(null)
  const [constructing, setConstructing] = useState(false)

  useEffect(() => {
    if (!campaignId) return
    api.getBuildings(campaignId).then(res => {
      const data = (res as any).buildings
      setBuildings(data)
    }).catch(() => {
      setBuildings({ buildings: [], total_slots: 5 })
    })
  }, [campaignId])

  const handleConstruct = async (buildingId: string) => {
    setConstructing(true)
    try {
      await api.construct(campaignId, buildingId)
      const res = await api.getBuildings(campaignId)
      setBuildings((res as any).buildings)
    } catch (e) {
      console.error(e)
    }
    setConstructing(false)
  }

  const buildingList = buildings?.buildings || []
  const totalSlots = buildings?.total_slots || 5

  return (
    <div className="fade-in">
      <div className="buildings-header">
        <span className="buildings-slots">建筑槽位: {buildingList.filter(b => b.constructed).length}/{totalSlots}</span>
      </div>

      <div className="buildings-grid">
        {buildingList.map(b => (
          <div key={b.id} className={`building-card ${b.constructed ? 'building-card--built' : ''}`}>
            <div className="building-card__header">
              <span className="building-card__name">{b.name}</span>
              {b.constructed && <span className="building-card__level">Lv.{b.level}</span>}
            </div>
            <div className="building-card__effect">{b.effect_str}</div>
            {!b.constructed && (
              <button type="button"
                className="btn btn--primary building-card__build"
                onClick={() => handleConstruct(b.id)}
                disabled={constructing || buildingList.filter(x => x.constructed).length >= totalSlots}
              >
                {b.cost > 0 ? `建造 (${b.cost}万两)` : '建造'}
              </button>
            )}
          </div>
        ))}
      </div>

      {buildingList.length === 0 && (
        <div className="empty-state">
          <p>暂无建筑数据</p>
        </div>
      )}
    </div>
  )
}
