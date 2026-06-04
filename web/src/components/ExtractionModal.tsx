/* =============================================
   ExtractionModal - 提取章节透明 (v5.1.2 P2-3)
   v5.1 内部设计 ExtractionModal, 4 档房 Tab + 折叠 JSON
   ============================================= */
import { useEffect, useRef, useState } from 'react'
import { X, ChevronDown, ChevronRight, FileJson, AlertCircle } from 'lucide-react'

type Tier = 'internal' | 'issues' | 'military_external' | 'personnel_secret'

const TIER_LABEL: Record<Tier, string> = {
  internal: '主控 (内部)',
  issues: '局势 (事项)',
  military_external: '军外 (军事/外部)',
  personnel_secret: '人事 (密令)',
}

const TIER_DESC: Record<Tier, string> = {
  internal: 'metric_delta / economy_moves / fiscal_changes / faction_delta / class_delta / region_delta',
  issues: 'issue_advances / new_issues / cancels / close_issues',
  military_external: 'army_delta / new_armies / power_updates / world_advance',
  personnel_secret: 'office_changes / appointments / character_status_changes / character_power_changes / secret_order_updates / secret_order_closes',
}

const TIER_PROMPT_FILE: Record<Tier, string> = {
  internal: 'content/prompts/score_extractor_internal.md',
  issues: 'content/prompts/score_extractor_issues.md',
  military_external: 'content/prompts/score_extractor_military_external.md',
  personnel_secret: 'content/prompts/score_extractor_personnel_secret.md',
}

interface TierData {
  prompt?: string
  output: string
}

interface ExtractionData {
  turn: number
  tiers: Record<Tier, TierData>
  summary?: { decree_length: number; narrative_length: number; has_output: boolean }
}

interface ExtractionModalProps {
  open: boolean
  data: ExtractionData | null
  onClose: () => void
}

export function ExtractionModal({ open, data, onClose }: ExtractionModalProps) {
  const [tier, setTier] = useState<Tier>('internal')
  const [promptOpen, setPromptOpen] = useState(false)
  const [outputOpen, setOutputOpen] = useState(true)
  const bodyRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  useEffect(() => {
    setPromptOpen(false)
    setOutputOpen(true)
  }, [tier, open])

  if (!open || !data) return null

  const tierData = data.tiers?.[tier] || { prompt: '', output: '' }
  const hasOutput = !!tierData.output

  return (
    <div className="extract-modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="提取章节">
      <div className="extract-modal" onClick={(e) => e.stopPropagation()}>
        <div className="extract-modal__titlebar">
          <div className="extract-modal__title">
            <FileJson size={18} />
            <span>提取透明 · T{data.turn}</span>
          </div>
          <button type="button" className="extract-modal__close" onClick={onClose} aria-label="关闭">
            <X size={16} />
            <span>关闭</span>
          </button>
        </div>

        <div className="extract-modal__tabs" role="tablist">
          {(Object.keys(TIER_LABEL) as Tier[]).map((t) => (
            <button
              key={t}
              type="button"
              role="tab"
              aria-selected={tier === t}
              className={`extract-tab ${tier === t ? 'extract-tab--active' : ''}`}
              onClick={() => setTier(t)}
            >
              {TIER_LABEL[t]}
            </button>
          ))}
        </div>

        <div className="extract-modal__desc">
          {TIER_DESC[tier]}
        </div>

        <div className="extract-modal__body" ref={bodyRef}>
          {/* Prompt 折叠 */}
          <div className="extract-section">
            <button
              type="button"
              className="extract-section__head"
              onClick={() => setPromptOpen(!promptOpen)}
              aria-expanded={promptOpen}
            >
              {promptOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              <span>Prompt 模板</span>
              <code className="extract-section__path">{TIER_PROMPT_FILE[tier]}</code>
            </button>
            {promptOpen && (
              <pre className="extract-section__content extract-prompt">
                {tierData.prompt || '(prompt 文件路径: ' + TIER_PROMPT_FILE[tier] + ')'}
              </pre>
            )}
          </div>

          {/* Output 折叠 */}
          <div className="extract-section">
            <button
              type="button"
              className="extract-section__head"
              onClick={() => setOutputOpen(!outputOpen)}
              aria-expanded={outputOpen}
            >
              {outputOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              <span>输出 JSON</span>
              <span className="extract-section__meta">
                {hasOutput ? `${tierData.output.length} 字` : '无记录'}
              </span>
            </button>
            {outputOpen && (
              hasOutput ? (
                <pre className="extract-section__content extract-output">
                  {tierData.output}
                </pre>
              ) : (
                <div className="extract-empty">
                  <AlertCircle size={16} />
                  <span>本 turn 无 extraction 记录 (extract_score 未运行或未存储)</span>
                </div>
              )
            )}
          </div>
        </div>

        {data.summary && (
          <div className="extract-modal__footer">
            <span>诏书长度: {data.summary.decree_length} 字</span>
            <span>·</span>
            <span>奏章长度: {data.summary.narrative_length} 字</span>
            <span>·</span>
            <span>提取器输出: {data.summary.has_output ? '有' : '无'}</span>
          </div>
        )}
      </div>
    </div>
  )
}
