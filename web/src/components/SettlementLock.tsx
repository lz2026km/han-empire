import { useState, useEffect, useRef } from 'react'
import { X, ChevronRight, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface SettlementStage {
  id: string
  name: string
  status: 'pending' | 'processing' | 'done'
}

interface ValueChange {
  label: string
  oldValue: number
  newValue: number
  change: number
}

interface SettlementLockProps {
  isOpen: boolean
  onClose: () => void
  month: number
  year: number
  stages: SettlementStage[]
  currentStage: string
  onStageComplete: (stageId: string) => void
  changes: Record<string, ValueChange[]>
}

type StageType = 'stage' | 'thinking' | 'text' | 'done'

export function SettlementLock({
  isOpen,
  onClose,
  month,
  year,
  stages: initialStages,
  currentStage,
  changes
}: SettlementLockProps) {
  const [displayedText, setDisplayedText] = useState('')
  const [fullText, setFullText] = useState('')
  const [activeStage, setActiveStage] = useState<string>(currentStage)
  const [stageType, setStageType] = useState<StageType>('stage')
  const [showDone, setShowDone] = useState(false)
  const contentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (currentStage) {
      setActiveStage(currentStage)
      if (currentStage === 'done') {
        setShowDone(true)
      } else {
        const stage = initialStages.find(s => s.id === currentStage)
        if (stage) {
          const text = `【${stage.name}】`
          setFullText(text)
          setDisplayedText('')
          setStageType('stage')
          typeText(text)
        }
      }
    }
  }, [currentStage, initialStages])

  useEffect(() => {
    if (stageType === 'thinking') {
      const thoughts = [
        '计算中...',
        '推演中...',
        '分析中...',
      ]
      let i = 0
      const interval = setInterval(() => {
        setDisplayedText(thoughts[i % thoughts.length] + '▊')
        i++
      }, 200)
      const timeout = setTimeout(() => {
        clearInterval(interval)
        setDisplayedText('')
      }, 1500)
      return () => {
        clearInterval(interval)
        clearTimeout(timeout)
      }
    }
  }, [stageType])

  const typeText = (text: string) => {
    let i = 0
    const interval = setInterval(() => {
      if (i <= text.length) {
        setDisplayedText(text.slice(0, i))
        i++
      } else {
        clearInterval(interval)
        contentRef.current?.scrollIntoView({ behavior: 'smooth' })
      }
    }, 50)
  }

  const formatChange = (change: number) => {
    if (change > 0) return `+${change}`
    if (change < 0) return `${change}`
    return '0'
  }

  const getChangeIcon = (change: number) => {
    if (change > 0) return <TrendingUp size={14} className="change-icon change-icon--up" />
    if (change < 0) return <TrendingDown size={14} className="change-icon change-icon--down" />
    return <Minus size={14} className="change-icon change-icon--neutral" />
  }

  const allChanges = Object.entries(changes).flatMap(([category, items]) =>
    items.map(item => ({ ...item, category }))
  )

  if (!isOpen) return null

  return (
    <div className="modal-overlay settlement-lock-overlay">
      <div className="settlement-lock">
        <div className="settlement-lock__header">
          <div className="settlement-lock__title">
            <span>📊 月末结算</span>
            <span className="settlement-lock__date">
              {year}年 {month + 1}月
            </span>
          </div>
          {!showDone && (
            <button className="settlement-lock__close" onClick={onClose}>
              <X size={20} />
            </button>
          )}
        </div>

        <div className="settlement-lock__body" ref={contentRef}>
          {!showDone ? (
            <>
              <div className="settlement-lock__stages">
                {initialStages.map((stage, index) => (
                  <div
                    key={stage.id}
                    className={`settlement-lock__stage ${
                      stage.id === activeStage ? 'settlement-lock__stage--active' : ''
                    } ${
                      initialStages.findIndex(s => s.id === activeStage) > index
                        ? 'settlement-lock__stage--done'
                        : ''
                    }`}
                  >
                    <div className="settlement-lock__stage-dot">
                      {initialStages.findIndex(s => s.id === activeStage) > index ? (
                        '✓'
                      ) : (
                        <ChevronRight size={12} />
                      )}
                    </div>
                    <span>{stage.name}</span>
                  </div>
                ))}
              </div>

              <div className="settlement-lock__content">
                <div className="settlement-lock__text">
                  {displayedText}
                  {stageType === 'thinking' && <span className="settlement-lock__cursor">▊</span>}
                </div>
              </div>
            </>
          ) : (
            <div className="settlement-lock__done">
              <div className="settlement-lock__done-title">本月结算完成</div>
              <div className="settlement-lock__changes">
                <div className="settlement-lock__changes-header">数值变化</div>
                {allChanges.length === 0 ? (
                  <div className="settlement-lock__no-changes">本月无显著变化</div>
                ) : (
                  <div className="settlement-lock__changes-list">
                    {allChanges.map((change, index) => (
                      <div key={index} className="settlement-lock__change-item">
                        <span className="settlement-lock__change-label">{change.label}</span>
                        <span className="settlement-lock__change-values">
                          <span className="settlement-lock__change-old">{change.oldValue}</span>
                          <span className="settlement-lock__change-arrow">→</span>
                          <span className="settlement-lock__change-new">{change.newValue}</span>
                        </span>
                        <span className={`settlement-lock__change-delta settlement-lock__change-delta--${change.change > 0 ? 'up' : change.change < 0 ? 'down' : 'neutral'}`}>
                          {getChangeIcon(change.change)}
                          {formatChange(change.change)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="settlement-lock__actions">
                <button className="btn btn--primary" onClick={onClose}>
                  进入下月
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}