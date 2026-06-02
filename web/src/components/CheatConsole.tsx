import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { X, Terminal, Activity, Layers, ListChecks, ChevronRight, AlertCircle, CheckCircle } from 'lucide-react'
import { api } from '../api'

interface CommandResult {
  command: string
  output: string
  success: boolean
  timestamp: string
}

interface DebugState {
  campaign_id: string
  turn: number
  year: number
  period: number
  metrics: Record<string, number>
  factions: Array<{ name: string; satisfaction: number; leverage: number; agenda?: string }>
  issues: Array<{ id: number; kind: string; status: string; title: string; origin_turn: number }>
  ministers_count: number
  ministers_sample: Array<{ name: string; office: string; faction: string; loyalty: number; ability: number }>
}

interface CommandMeta { cmd: string; cat: string; desc: string }
interface CommandsResponse { commands: CommandMeta[]; presets: string[] }

type Tab = 'console' | 'state' | 'scenarios' | 'commands'

interface CheatConsoleProps {
  isOpen: boolean
  onClose: () => void
  onExecuteCommand: (command: string) => Promise<{ success: boolean; output: string }>
  campaignId: string | null
}

const CAT_LABEL: Record<string, string> = {
  meta: '元命令', inspect: '状态检视', scenario: '场景加载',
  metric: '指标调控', time: '时间调控', event: '事件注入',
}

const SCENARIO_DESC: Record<string, string> = {
  caotang_ruin: '董卓焚洛阳 (189年6月)',
  yidai_200: '衣带诏事发前夕 (200年4月)',
  guandu_202: '官渡之战前夕 (202年9月)',
  chibi_208: '赤壁之战前夕 (208年11月)',
  caopi_220: '曹丕篡汉 (220年10月)',
}

export function CheatConsole({ isOpen, onClose, onExecuteCommand, campaignId }: CheatConsoleProps) {
  const [tab, setTab] = useState<Tab>('console')
  const [input, setInput] = useState('')
  const [history, setHistory] = useState<CommandResult[]>([])
  const [executing, setExecuting] = useState(false)
  const [commandHistory, setCommandHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)

  const [state, setState] = useState<DebugState | null>(null)
  const [stateLoading, setStateLoading] = useState(false)
  const [meta, setMeta] = useState<CommandsResponse | null>(null)
  const [stateError, setStateError] = useState<string | null>(null)

  const inputRef = useRef<HTMLInputElement>(null)
  const historyEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen && inputRef.current) inputRef.current.focus()
  }, [isOpen, tab])

  useEffect(() => {
    historyEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history])

  useEffect(() => {
    if (!isOpen) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [isOpen, onClose])

  useEffect(() => {
    if (!isOpen || !campaignId) return
    if (tab === 'state' && !state) {
      setStateLoading(true)
      setStateError(null)
      api.getDebugState(campaignId)
        .then(s => setState(s))
        .catch(e => setStateError(e.message))
        .finally(() => setStateLoading(false))
    }
    if (tab === 'commands' && !meta) {
      api.getDebugCommands(campaignId)
        .then(m => setMeta(m))
        .catch(e => setStateError(e.message))
    }
  }, [tab, isOpen, campaignId, state, meta])

  const refreshState = useCallback(async () => {
    if (!campaignId) return
    setStateLoading(true)
    setStateError(null)
    try {
      const s = await api.getDebugState(campaignId)
      setState(s)
    } catch (e: any) {
      setStateError(e.message)
    } finally {
      setStateLoading(false)
    }
  }, [campaignId])

  const handleExecute = useCallback(async (cmd: string) => {
    if (!cmd.trim() || executing) return
    const trimmed = cmd.trim()
    const timestamp = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

    if (trimmed === 'clear') { setHistory([]); setInput(''); return }
    if (trimmed === 'exit') { onClose(); return }

    setExecuting(true)
    try {
      const result = await onExecuteCommand(trimmed)
      setHistory(prev => [...prev, { command: trimmed, output: result.output, success: result.success, timestamp }])
      if (trimmed.startsWith('add-') || trimmed.startsWith('set-') || trimmed.startsWith('scenario') || trimmed === 'inspect' || trimmed === 'status') {
        refreshState().catch(() => undefined)
      }
    } catch {
      setHistory(prev => [...prev, { command: trimmed, output: '命令执行失败', success: false, timestamp }])
    }
    setExecuting(false)
    setInput('')
  }, [executing, onExecuteCommand, onClose, refreshState])

  const runAndRefresh = useCallback(async (cmd: string) => {
    setTab('console')
    await handleExecute(cmd)
  }, [handleExecute])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleExecute(input)
      if (input.trim()) setCommandHistory(prev => [input, ...prev.slice(0, 49)])
      setHistoryIndex(-1)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (historyIndex < commandHistory.length - 1) {
        const idx = historyIndex + 1
        setHistoryIndex(idx)
        setInput(commandHistory[idx])
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (historyIndex > 0) {
        const idx = historyIndex - 1
        setHistoryIndex(idx)
        setInput(commandHistory[idx])
      } else if (historyIndex === 0) {
        setHistoryIndex(-1)
        setInput('')
      }
    }
  }

  const quickActions = useMemo(() => [
    { label: '状态', cmd: 'inspect' },
    { label: '+10 威权', cmd: 'add-authority 10' },
    { label: '+20 声望', cmd: 'add-loyalty 20' },
    { label: '+50 财政', cmd: 'add-metric 汉室库 50' },
    { label: '推进一月', cmd: 'skip-month' },
    { label: '推进一年', cmd: 'skip-year' },
  ], [])

  if (!isOpen) return null

  return (
    <div className="cheat-console-overlay" onClick={onClose}>
      <div className="cheat-console cheat-console--engineer" onClick={e => e.stopPropagation()}>
        <div className="cheat-console__header">
          <div className="cheat-console__title">
            <Terminal size={16} />
            <span>工程师控制台</span>
            {campaignId && <span className="cheat-console__cid">cid: {campaignId.slice(0, 8)}</span>}
          </div>
          <button type="button" className="cheat-console__close" onClick={onClose} aria-label="关闭">
            <X size={16} />
          </button>
        </div>

        <div className="cheat-console__tabs" role="tablist">
          <button type="button" role="tab" aria-selected={tab==='console'} className={`cheat-console__tab ${tab==='console'?'cheat-console__tab--active':''}`} onClick={() => setTab('console')}>
            <Terminal size={14} /> 控制台
          </button>
          <button type="button" role="tab" aria-selected={tab==='state'} className={`cheat-console__tab ${tab==='state'?'cheat-console__tab--active':''}`} onClick={() => setTab('state')}>
            <Activity size={14} /> 状态检视
          </button>
          <button type="button" role="tab" aria-selected={tab==='scenarios'} className={`cheat-console__tab ${tab==='scenarios'?'cheat-console__tab--active':''}`} onClick={() => setTab('scenarios')}>
            <Layers size={14} /> 场景加载
          </button>
          <button type="button" role="tab" aria-selected={tab==='commands'} className={`cheat-console__tab ${tab==='commands'?'cheat-console__tab--active':''}`} onClick={() => setTab('commands')}>
            <ListChecks size={14} /> 命令参考
          </button>
        </div>

        {tab === 'console' && (
          <div className="cheat-console__body">
            <div className="cheat-console__quickbar">
              {quickActions.map(qa => (
                <button type="button" key={qa.label} className="cheat-console__quick" onClick={() => runAndRefresh(qa.cmd)} disabled={executing}>
                  {qa.label}
                </button>
              ))}
            </div>
            <div className="cheat-console__output">
              {history.length === 0 && (
                <div className="cheat-console__welcome">
                  <p>汉帝国 工程师调试控制台</p>
                  <p className="cheat-console__welcome-hint">输入 help 查命令, 点上方快捷按钮或切到「场景加载/状态检视/命令参考」面板</p>
                </div>
              )}
              {history.map((entry, index) => (
                <div key={index} className="cheat-console__entry">
                  <div className="cheat-console__entry-header">
                    <span className="cheat-console__prompt">$</span>
                    <span className="cheat-console__command">{entry.command}</span>
                    <span className="cheat-console__time">{entry.timestamp}</span>
                  </div>
                  <div className={`cheat-console__result ${entry.success ? 'cheat-console__result--success' : 'cheat-console__result--error'}`}>
                    <pre>{entry.output}</pre>
                  </div>
                </div>
              ))}
              {executing && (
                <div className="cheat-console__entry">
                  <div className="cheat-console__entry-header">
                    <span className="cheat-console__prompt">$</span>
                    <span className="cheat-console__command">{input}</span>
                  </div>
                  <div className="cheat-console__result cheat-console__result--executing">执行中...</div>
                </div>
              )}
              <div ref={historyEndRef} />
            </div>
            <div className="cheat-console__input-area">
              <span className="cheat-console__prompt">$</span>
              <input
                ref={inputRef}
                type="text"
                className="cheat-console__input"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入命令 (例: add-authority 20, scenario chibi_208)"
                autoComplete="off"
                disabled={executing}
              />
            </div>
          </div>
        )}

        {tab === 'state' && (
          <div className="cheat-console__body cheat-console__body--panel">
            {stateError && <div className="cheat-console__error">加载失败: {stateError}</div>}
            {stateLoading && !state && <div className="cheat-console__loading">正在加载状态...</div>}
            {state && (
              <>
                <div className="cheat-console__state-header">
                  <div>
                    <div className="cheat-console__state-title">{state.year}年{state.period}月 · 回合 {state.turn}</div>
                    <div className="cheat-console__state-sub">campaign {state.campaign_id.slice(0, 8)} · 汉廷在任大臣 {state.ministers_count} · 事项 {state.issues.length} · 派系 {state.factions.length}</div>
                  </div>
                  <button type="button" className="cheat-console__quick" onClick={refreshState} disabled={stateLoading}>
                    刷新
                  </button>
                </div>

                <div className="cheat-console__metrics">
                  {Object.entries(state.metrics)
                    .filter(([, v]) => typeof v === 'number')
                    .sort((a, b) => Math.abs(b[1] as number) - Math.abs(a[1] as number))
                    .map(([k, v]) => (
                      <div key={k} className="cheat-console__metric">
                        <div className="cheat-console__metric-label">{k}</div>
                        <div className="cheat-console__metric-value">{v as number}</div>
                        <div className="cheat-console__metric-actions">
                          <button type="button" onClick={() => runAndRefresh(`add-metric ${k} 5`)}>+5</button>
                          <button type="button" onClick={() => runAndRefresh(`add-metric ${k} 10`)}>+10</button>
                          <button type="button" onClick={() => runAndRefresh(`add-metric ${k} -5`)}>-5</button>
                        </div>
                      </div>
                    ))}
                </div>

                <div className="cheat-console__state-section">
                  <h4>派系 ({state.factions.length})</h4>
                  {state.factions.length === 0 ? <div className="cheat-console__muted">暂无派系数据</div> : (
                    <table className="cheat-console__table">
                      <thead><tr><th>名称</th><th>满意度</th><th>影响力</th><th>议程</th></tr></thead>
                      <tbody>
                        {state.factions.map(f => (
                          <tr key={f.name}>
                            <td>{f.name}</td>
                            <td>{f.satisfaction}</td>
                            <td>{f.leverage}</td>
                            <td className="cheat-console__muted">{f.agenda || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>

                <div className="cheat-console__state-section">
                  <h4>近期事项 (top {state.issues.length})</h4>
                  {state.issues.length === 0 ? <div className="cheat-console__muted">暂无事项</div> : (
                    <ul className="cheat-console__list">
                      {state.issues.map(i => (
                        <li key={i.id}>
                          <span className="cheat-console__tag">#{i.id}</span>
                          <span className="cheat-console__tag cheat-console__tag--{i.status}">{i.status}</span>
                          <span className="cheat-console__tag cheat-console__tag--muted">T{i.origin_turn}</span>
                          <span className="cheat-console__tag cheat-console__tag--kind">{i.kind}</span>
                          <span>{i.title}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div className="cheat-console__state-section">
                  <h4>大臣示例 (前 {state.ministers_sample.length})</h4>
                  <table className="cheat-console__table">
                    <thead><tr><th>姓名</th><th>官职</th><th>派系</th><th>忠诚</th><th>能力</th></tr></thead>
                    <tbody>
                      {state.ministers_sample.map(m => (
                        <tr key={m.name}>
                          <td>{m.name}</td>
                          <td>{m.office}</td>
                          <td>{m.faction}</td>
                          <td>{m.loyalty}</td>
                          <td>{m.ability}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        )}

        {tab === 'scenarios' && (
          <div className="cheat-console__body cheat-console__body--panel">
            <div className="cheat-console__hint">预设场景: 一键跳转至汉末关键时刻, 状态和指标会同步更新</div>
            <div className="cheat-console__scenarios">
              {Object.entries(SCENARIO_DESC).map(([key, desc]) => (
                <div key={key} className="cheat-console__scenario" role="button" tabIndex={0}
                  onClick={() => runAndRefresh(`scenario ${key}`)}
                  onKeyDown={e => { if (e.key === 'Enter') runAndRefresh(`scenario ${key}`) }}>
                  <div className="cheat-console__scenario-name">{key}</div>
                  <div className="cheat-console__scenario-desc">{desc}</div>
                  <ChevronRight size={16} className="cheat-console__scenario-arrow" />
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === 'commands' && (
          <div className="cheat-console__body cheat-console__body--panel">
            {!meta && <div className="cheat-console__loading">加载命令列表...</div>}
            {meta && (
              <div className="cheat-console__commands">
                {(['meta', 'inspect', 'scenario', 'metric', 'time', 'event'] as const).map(cat => {
                  const items = meta.commands.filter(c => c.cat === cat)
                  if (items.length === 0) return null
                  return (
                    <div key={cat} className="cheat-console__cmdgroup">
                      <h4>{CAT_LABEL[cat] || cat}</h4>
                      <ul>
                        {items.map(c => (
                          <li key={c.cmd}>
                            <button type="button" className="cheat-console__cmd" onClick={() => setInput(c.cmd)} title="点击填入">
                              <code>{c.cmd}</code>
                              <span className="cheat-console__cmd-desc">{c.desc}</span>
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )
                })}
                <div className="cheat-console__hint" style={{ marginTop: 16 }}>
                  提示: 点击命令填入输入框, 回车执行; 状态变化会同步到「状态检视」面板
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
