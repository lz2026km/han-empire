/* =============================================
   SettingsModal - 设置弹窗 (v5.2.0 P6-7)
   4 段: 主题 / 季节 / 快捷键 / 关于
   ============================================= */
import { useEffect, useState } from 'react'
import { Sun, Moon, Cloud, Flower, Leaf, Snowflake, Keyboard, Info, Save, Trash2 } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'
import { api } from '../api'

interface SettingsModalProps {
  open: boolean
  onClose: () => void
  onClearSaves?: () => void
  // v5.2.0 P6-8: 嵌套 StatsModal
  onOpenStats?: () => void
}

const SHORTCUTS: { keys: string; desc: string }[] = [
  { keys: '1-9', desc: '切换前 9 个 Tab (总览/诏书/召对/大臣/派系/技能/建筑/地图/密令)' },
  { keys: 'L / C', desc: '切换 日志 / 后宫 Tab' },
  { keys: 'S', desc: '弹 国势详情 弹窗' },
  { keys: 'H', desc: '弹 回合历史 弹窗' },
  { keys: 'E', desc: '弹 提取透明 弹窗' },
  { keys: '?', desc: '弹 帮助 弹窗' },
  { keys: 'Esc', desc: '关闭弹窗 / 游戏中返回主菜单 (二次确认)' },
  { keys: 'Ctrl+`', desc: '弹 工程师控制台 (cheat)' },
]

export function SettingsModal({ open, onClose, onClearSaves, onOpenStats }: SettingsModalProps) {
  const { theme, setTheme, season, cycleSeason } = useTheme()
  const [stats, setStats] = useState<any>(null)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  useEffect(() => {
    if (!open) return
    api.getStatsGlobal?.().then(setStats).catch(() => setStats(null))
  }, [open])

  if (!open) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '640px' }}>
        <div className="modal__title">设置</div>

        {/* 主题 */}
        <section className="settings-section">
          <h3>主题</h3>
          <div className="settings-row">
            <button
              type="button"
              className={`btn ${theme === 'dark' ? 'btn--primary' : ''}`}
              onClick={() => setTheme('dark')}
            >
              <Moon size={14} /> 玄黑 (默认)
            </button>
            <button
              type="button"
              className={`btn ${theme === 'light' ? 'btn--primary' : ''}`}
              onClick={() => setTheme('light')}
            >
              <Sun size={14} /> 亮色
            </button>
          </div>
        </section>

        {/* 季节 */}
        <section className="settings-section">
          <h3>季节 (背景)</h3>
          <div className="settings-row">
            {(['spring', 'summer', 'autumn', 'winter'] as const).map(s => (
              <button
                key={s}
                type="button"
                className={`btn ${season === s ? 'btn--primary' : ''}`}
                onClick={() => cycleSeason()}
                data-tooltip={`当前: ${season}`}
              >
                {s === 'spring' && <Flower size={14} />}
                {s === 'summer' && <Cloud size={14} />}
                {s === 'autumn' && <Leaf size={14} />}
                {s === 'winter' && <Snowflake size={14} />}
                {s === 'spring' ? '春' : s === 'summer' ? '夏' : s === 'autumn' ? '秋' : '冬'}
              </button>
            ))}
          </div>
          <p style={{ fontSize: '11px', color: 'var(--color-text-muted)', margin: '6px 0 0' }}>
            点击任一按钮可循环切换季节; 当前: {season}
          </p>
        </section>

        {/* 快捷键 */}
        <section className="settings-section">
          <h3><Keyboard size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} /> 快捷键</h3>
          <div className="settings-shortcut-list">
            {SHORTCUTS.map(s => (
              <div key={s.keys} className="settings-shortcut-row">
                <kbd className="settings-kbd">{s.keys}</kbd>
                <span>{s.desc}</span>
              </div>
            ))}
          </div>
        </section>

        {/* 多周目统计 (from v5.1.5 P5-1) */}
        <section className="settings-section">
          <h3><Info size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} /> 多周目统计</h3>
          {stats ? (
            <div className="settings-stats">
              <div><b>总局数</b>: {stats.total_runs}</div>
              <div><b>胜</b>: {stats.wins} / <b>负</b>: {stats.losses}</div>
              <div><b>结局解锁</b>: {stats.endings_unlocked?.length || 0} 种</div>
            </div>
          ) : (
            <p style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
              (暂无统计数据, 完成首局后可见)
            </p>
          )}
          {onOpenStats && (
            <button
              type="button"
              className="btn"
              onClick={() => { onOpenStats(); onClose() }}
              style={{ marginTop: '8px' }}
            >
              查看完整战绩 →
            </button>
          )}
        </section>

        {/* 关于 */}
        <section className="settings-section">
          <h3>关于</h3>
          <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', lineHeight: 1.7 }}>
            <b>汉献帝之末路 v5.2.0</b> — 回合制汉风政治游戏 的回合制汉风政治游戏。<br />
            主公将以献帝身份, 在 189-220 年的乱局中求存。<br />
            <span style={{ color: 'var(--color-text-muted)' }}>
              灵感: 陈舜臣《三国》、罗贯中《三国演义》、v5.1 内部设计 汉末汉献帝
            </span>
          </p>
        </section>

        {/* 危险区 */}
        {onClearSaves && (
          <section className="settings-section settings-section--danger">
            <h3>危险操作</h3>
            <button
              type="button"
              className="btn btn--danger"
              onClick={onClearSaves}
            >
              <Trash2 size={14} /> 清空所有存档
            </button>
            <Save size={14} style={{ marginLeft: 8, color: 'var(--color-text-muted)' }} />
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>主公慎用</span>
          </section>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '12px' }}>
          <button type="button" className="btn btn--primary" onClick={onClose}>关闭</button>
        </div>
      </div>
    </div>
  )
}
