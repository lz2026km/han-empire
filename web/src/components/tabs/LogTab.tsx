// v2.0.0 Phase 3.1: 起居注 Tab - 抽自 App.tsx:846-860 (15 行)
// 汉风命名（原"日志"）—— 帝王起居注是东汉三国史料传统
interface LogEntry {
  time: string
  text: string
  important?: boolean
}

export function LogTab({ entries }: { entries: LogEntry[] }) {
  return (
    <div className="fade-in">
      <div className="card" style={{ padding: '0', maxHeight: '500px', overflow: 'auto' }}>
        {entries.length === 0 && <div className="empty-state">暂无起居</div>}
        {entries.map((entry, i) => (
          <div key={i} className={`log-entry ${entry.important ? 'log-entry--important' : ''}`}>
            <span className="log-entry__time">[{entry.time}]</span>
            <span className="log-entry__text">{entry.text}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
