/* =============================================
   LoadingScreen - 全屏推演 Loading (v5.2.0 P6-6)
   仿 ming_sim simulate_loading, 月相轮转 + 古风文案
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

interface LoadingScreenProps {
  open: boolean
  title?: string
}

export function LoadingScreen({ open, title = '推演中' }: LoadingScreenProps) {
  const [phaseIdx, setPhaseIdx] = useState(0)

  useEffect(() => {
    if (!open) {
      setPhaseIdx(0)
      return
    }
    const t = setInterval(() => {
      setPhaseIdx(i => (i + 1) % PHASES.length)
    }, 1600)
    return () => clearInterval(t)
  }, [open])

  if (!open) return null

  const phase = PHASES[phaseIdx]

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
