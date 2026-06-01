// v2.0.0 Phase 3.2: useSettlement hook - 抽自 App.tsx:131-184 (55 行)
// "三国/汉风"视角：4 阶段结算（财政/藩镇/事件/叙事）= 模拟古代朝政月度会审
import { useState, useRef, useCallback, useEffect } from 'react'
import { api } from '../api'

export interface SettlementStage {
  id: string
  name: string
  status: 'pending' | 'active' | 'done'
}

const DEFAULT_STAGES: SettlementStage[] = [
  { id: 'fiscal', name: '财政结算', status: 'pending' },
  { id: 'faction', name: '藩镇变化', status: 'pending' },
  { id: 'events', name: '事件触发', status: 'pending' },
  { id: 'narrative', name: '叙事生成', status: 'pending' },
]

/**
 * 抽自 App.tsx handleStreamSettlement (L131-184)
 * 暴露：showSettlement / settlementStages / currentSettlementStage + startSettlement
 * v2.0.0 P0-B4: useRef + useEffect cleanup 关闭 SSE 防组件 unmount 后泄漏
 */
export function useSettlement(campaignId: string | null) {
  const [showSettlement, setShowSettlement] = useState(false)
  const [settlementStages, setSettlementStages] = useState<SettlementStage[]>(DEFAULT_STAGES)
  const [currentSettlementStage, setCurrentSettlementStage] = useState<string>('fiscal')
  const eventSourceRef = useRef<EventSource | null>(null)

  const startSettlement = useCallback(async () => {
    if (!campaignId) return
    setShowSettlement(true)
    setSettlementStages(DEFAULT_STAGES)
    setCurrentSettlementStage('fiscal')

    try {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
      const eventSource = api.streamSettlement(campaignId)
      eventSourceRef.current = eventSource

      eventSource.addEventListener('stage', (e: any) => {
        const data = JSON.parse(e.data)
        if (data.stage === 'thinking') {
          setCurrentSettlementStage(data.stage)
        } else {
          const stageId = data.stage.replace('_done', '')
          setCurrentSettlementStage(stageId)
          setSettlementStages(prev => prev.map(s =>
            s.id === stageId ? { ...s, status: 'done' } : s
          ))
        }
      })

      eventSource.addEventListener('done', () => {
        eventSource.close()
        eventSourceRef.current = null
        setShowSettlement(false)
      })

      eventSource.addEventListener('error', () => {
        eventSource.close()
        eventSourceRef.current = null
        setShowSettlement(false)
      })
    } catch (e) {
      setShowSettlement(false)
    }
  }, [campaignId])

  // v2.0.0 P0-B4: 组件 unmount 关闭 EventSource
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [])

  return {
    showSettlement,
    setShowSettlement,
    settlementStages,
    currentSettlementStage,
    startSettlement,
  }
}
