/* =============================================
   SettlementLock - 全屏锁推演组件 (v2.2.0 内部设计, v5.1.1 双栏)
   - 推演期间锁键盘
   - v5.1.1 升级: 双栏布局 (左推敲 / 右正文), v5.1 内部设计 SettlementLock
   - 自动滚到底
   - 完成后显示「已颁布」+ 「退朝/退下」按钮
   ============================================= */
import { useEffect, useRef, useState } from 'react'
import { Loader2 } from 'lucide-react'

interface SettlementLockProps {
  stage: string
  thinking: string
  narrative: string
  decree?: string
  report?: any
  done: boolean
  error?: string
  onClose: () => void
}

export function SettlementLock({
  stage, thinking, narrative, decree, report, done, error, onClose,
}: SettlementLockProps) {
  const thinkRef = useRef<HTMLDivElement>(null)
  const narrRef = useRef<HTMLDivElement>(null)
  const [exiting, setExiting] = useState(false)

  // 锁键盘
  useEffect(() => {
    if (done) return
    const block = (event: KeyboardEvent) => {
      event.preventDefault()
      event.stopPropagation()
    }
    window.addEventListener('keydown', block, true)
    return () => window.removeEventListener('keydown', block, true)
  }, [done])

  // 自动滚
  useEffect(() => {
    if (thinkRef.current) thinkRef.current.scrollTop = thinkRef.current.scrollHeight
  }, [thinking])
  useEffect(() => {
    if (narrRef.current) narrRef.current.scrollTop = narrRef.current.scrollHeight
  }, [narrative])

  const handleClose = () => {
    setExiting(true)
    setTimeout(onClose, 200)
  }

  return (
    <div className={`settlement-lock ${exiting ? 'settlement-lock--exiting' : ''}`}
         role="alertdialog" aria-modal="true" aria-label="推演中">
      <div className="settlement-lock-card">
        {!done ? (
          <>
            <Loader2 className="settlement-spin" size={28} />
            <h2>{stage || '推演中...'}</h2>
          </>
        ) : (
          <>
            <div className="settlement-done-icon">[OK]</div>
            <h2>推演完成</h2>
          </>
        )}

        {error && (
          <div className="settlement-error">
            <strong>[X] 错误：</strong>{error}
          </div>
        )}

        {/* v5.1.1 P1-2: 双栏布局 (左推敲 / 右正文), v5.1 内部设计 SettlementLock:1376-1427 */}
        <div className="settlement-two-col">
          <div className="settlement-col settlement-col--thinking">
            <div className="settlement-col-label">邸报房推敲</div>
            <div ref={thinkRef} className="settlement-col-content settlement-thinking">
              {thinking || '（暂无推敲）'}
            </div>
          </div>
          <div className="settlement-col settlement-col--narrative">
            <div className="settlement-col-label">月末奏章</div>
            <div ref={narrRef} className="settlement-col-content settlement-narrative">
              {narrative || '（暂无奏章）'}
            </div>
          </div>
        </div>

        {decree && done && (
          <div className="settlement-decree-final">
            <h3>【正式诏书】</h3>
            <pre>{decree}</pre>
          </div>
        )}

        {report && done && (
          <div className="settlement-report">
            <h3>统计 推演报告</h3>
            <ul>
              {Object.entries(report).map(([k, v]) => (
                <li key={k}><b>{k}:</b> {String(v)}</li>
              ))}
            </ul>
          </div>
        )}

        {done && (
          <div className="settlement-actions">
            <button type="button" className="btn btn--primary" onClick={handleClose}>
              {report?.no_decree ? '已退朝' : '已颁布'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
