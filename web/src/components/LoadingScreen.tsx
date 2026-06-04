/* =============================================
   LoadingScreen - 全屏推演 Loading (v5.2.0 P6-6)
   仿 ming_sim simulate_loading, 月相轮转 + 古风文案
   v5.3.0 P7-1: currentStage 联动 (fiscal/faction/events/narrative)
   ============================================= */
import { useEffect, useState } from 'react'
import { Loader2, Sparkles } from 'lucide-react'

const PHASES = [
  { label: '主公稍候...', desc: '正在推演本月天机' },
  { label: '群臣议事...', desc: '百官各陈己见' },
  { label: '诏书拟成...', desc: '天机运转, 阴阳调和' },
  { label: '边关急报...', desc: '烽火连三月, 家书抵万金' },
  { label: '月相轮转...', desc: '花开花落, 寒来暑往' },
]

// v5.3.0 P7-1: nextTurn 4 阶段映射 (fiscal/faction/events/narrative)
const STAGE_PHASE_MAP: Record<string, { label: string; desc: string; idx: number }> = {
  fiscal: { label: '财政结算...', desc: '调算府库盈虚, 截留分账', idx: 0 },
  faction: { label: '藩镇变化...', desc: '群雄此消彼长, 派系暗流', idx: 1 },
  events: { label: '事件触发...', desc: '天降祥瑞或灾异, 静候吉凶', idx: 2 },
  narrative: { label: '叙事生成...', desc: '太史秉笔, 落墨成篇', idx: 3 },
  thinking: { label: '天机推演...', desc: '主公稍候, 容臣细思', idx: 4 },
}

interface LoadingScreenProps {
  open: boolean
  title?: string
  // v5.3.0 P7-1: 当前阶段 (fiscal/faction/events/narrative/thinking)
  // 传入时覆盖内置轮播, 显示对应阶段文案
  currentStage?: string
}

export function LoadingScreen({ open, title = '推演中', currentStage }: LoadingScreenProps) {
  const [phaseIdx, setPhaseIdx] = useState(0)

  useEffect(() => {
    if (!open) {
      setPhaseIdx(0)
      return
    }
    // v5.3.0 P7-1: 传 currentStage 时不轮播, 固定显示对应文案
    if (currentStage && STAGE_PHASE_MAP[currentStage]) {
      setPhaseIdx(STAGE_PHASE_MAP[currentStage].idx)
      return
    }
    const t = setInterval(() => {
      setPhaseIdx(i => (i + 1) % PHASES.length)
    }, 1600)
    return () => clearInterval(t)
  }, [open, currentStage])

  if (!open) return null

  // v5.3.0 P7-1: 优先用 stage 映射的 phase
  const phase = (currentStage && STAGE_PHASE_MAP[currentStage])
    ? STAGE_PHASE_MAP[currentStage]
    : PHASES[phaseIdx]

  return (
    <div className="loading-screen" role="status" aria-live="polite">
      <div className="loading-screen__bg" />
      <div className="loading-screen__panel">
        <div className="loading-screen__moon">
          <div className="loading-screen__moon-icon" />
          <div className="loading-screen__moon-icon loading-screen__moon-icon--2" />
          <div className="loading-screen__moon-icon loading-screen__moon-icon--3" />
        </div>
        <h2 className="loading-screen__title">{title}</h2>
        <div className="loading-screen__phase">
          <Sparkles size={14} style={{ marginRight: 4 }} />
          {phase.label}
        </div>
        <p className="loading-screen__desc">{phase.desc}</p>
        {/* v5.3.0 P7-1: 4 阶段进度指示 */}
        {currentStage && (
          <div className="loading-screen__stages">
            {(['fiscal', 'faction', 'events', 'narrative'] as const).map(s => {
              const active = s === currentStage
              const passedIdx = currentStage && STAGE_PHASE_MAP[currentStage]
                ? STAGE_PHASE_MAP[currentStage].idx : -1
              const sIdx = STAGE_PHASE_MAP[s].idx
              const passed = sIdx < passedIdx
              return (
                <div
                  key={s}
                  className={`loading-screen__stage ${active ? 'loading-screen__stage--active' : ''} ${passed ? 'loading-screen__stage--done' : ''}`}
                >
                  {STAGE_PHASE_MAP[s].label.replace('...', '')}
                </div>
              )
            })}
          </div>
        )}
        <div className="loading-screen__bar">
          <div className="loading-screen__bar-fill" />
        </div>
        <div className="loading-screen__hint">
          <Loader2 size={12} className="loading-screen__spin" />
          推演涉及 LLM 调用, 通常需 2-10 秒
        </div>
      </div>
    </div>
  )
}
