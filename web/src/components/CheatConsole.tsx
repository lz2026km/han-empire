import { useState, useEffect, useRef, useCallback } from 'react'
import { X, Terminal, ChevronRight, AlertCircle, CheckCircle } from 'lucide-react'

interface CommandResult {
  command: string
  output: string
  success: boolean
  timestamp: string
}

interface CheatConsoleProps {
  isOpen: boolean
  onClose: () => void
  onExecuteCommand: (command: string) => Promise<{ success: boolean; output: string }>
}

export function CheatConsole({ isOpen, onClose, onExecuteCommand }: CheatConsoleProps) {
  const [input, setInput] = useState('')
  const [history, setHistory] = useState<CommandResult[]>([])
  const [executing, setExecuting] = useState(false)
  const [commandHistory, setCommandHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const historyEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  useEffect(() => {
    historyEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history])

  const knownCommands = [
    { cmd: 'help', desc: '显示所有可用命令' },
    { cmd: 'status', desc: '显示当前游戏状态' },
    { cmd: 'add-authority <n>', desc: '增加威权值' },
    { cmd: 'add-loyalty <n>', desc: '增加忠诚度' },
    { cmd: 'add-minister <name>', desc: '添加大臣' },
    { cmd: 'set-authority <n>', desc: '设置威权值' },
    { cmd: 'unlock-skills', desc: '解锁所有技能' },
    { cmd: 'skip-month', desc: '跳过本月' },
    { cmd: 'reveal-map', desc: '显示所有省份' },
    { cmd: 'clear', desc: '清除控制台' },
    { cmd: 'exit', desc: '关闭控制台' },
  ]

  const handleExecute = useCallback(async (cmd: string) => {
    if (!cmd.trim() || executing) return

    const trimmedCmd = cmd.trim().toLowerCase()
    const timestamp = new Date().toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })

    if (trimmedCmd === 'clear') {
      setHistory([])
      setInput('')
      return
    }

    if (trimmedCmd === 'exit') {
      onClose()
      return
    }

    if (trimmedCmd === 'help') {
      const helpOutput = knownCommands
        .map(c => `  ${c.cmd.padEnd(20)} - ${c.desc}`)
        .join('\n')
      setHistory(prev => [...prev, {
        command: cmd,
        output: '可用命令:\n' + helpOutput,
        success: true,
        timestamp,
      }])
      setInput('')
      return
    }

    setExecuting(true)
    try {
      const result = await onExecuteCommand(trimmedCmd)
      setHistory(prev => [...prev, {
        command: cmd,
        output: result.output,
        success: result.success,
        timestamp,
      }])
    } catch {
      setHistory(prev => [...prev, {
        command: cmd,
        output: '命令执行失败',
        success: false,
        timestamp,
      }])
    }
    setExecuting(false)
    setInput('')
  }, [executing, onExecuteCommand, onClose])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleExecute(input)
      setCommandHistory(prev => [input, ...prev.slice(0, 49)])
      setHistoryIndex(-1)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (historyIndex < commandHistory.length - 1) {
        const newIndex = historyIndex + 1
        setHistoryIndex(newIndex)
        setInput(commandHistory[newIndex])
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1
        setHistoryIndex(newIndex)
        setInput(commandHistory[newIndex])
      } else if (historyIndex === 0) {
        setHistoryIndex(-1)
        setInput('')
      }
    }
  }

  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleGlobalKeyDown)
    return () => window.removeEventListener('keydown', handleGlobalKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="cheat-console-overlay" onClick={onClose}>
      <div className="cheat-console" onClick={e => e.stopPropagation()}>
        <div className="cheat-console__header">
          <div className="cheat-console__title">
            <Terminal size={16} />
            <span>控制台</span>
            <span className="cheat-console__hint">输入 help 查看命令</span>
          </div>
          <button type="button" className="cheat-console__close" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="cheat-console__body">
          <div className="cheat-console__output">
            {history.length === 0 && (
              <div className="cheat-console__welcome">
                <p>汉帝国 调试控制台</p>
                <p className="cheat-console__welcome-hint">输入 help 查看可用命令</p>
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
                <div className="cheat-console__result cheat-console__result--executing">
                  执行中...
                </div>
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
              placeholder="输入命令..."
              autoComplete="off"
            />
          </div>
        </div>
      </div>
    </div>
  )
}