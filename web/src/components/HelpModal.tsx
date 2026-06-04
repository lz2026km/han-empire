/* =============================================
   HelpModal - 帮助弹窗 (v5.2.0 P6-9)
   3 Tab: 玩法 / 快捷键 / 致谢
   ============================================= */
import { useEffect, useState } from 'react'
import { BookOpen, Keyboard, Heart, Crown, Scroll, Users, Sword, Building, Sparkles } from 'lucide-react'

type Tab = 'play' | 'shortcuts' | 'credits'

interface HelpModalProps {
  open: boolean
  onClose: () => void
}

const GAMEPLAY_SECTIONS: { icon: any; title: string; body: string }[] = [
  {
    icon: Crown,
    title: '开局',
    body: '主公以汉献帝刘协之身, 在 189-220 年的三国乱局中求存。初起威权仅 15, 藩镇高达 80, 必须步步为营。',
  },
  {
    icon: Scroll,
    title: '诏书',
    body: '通过颁布诏书推行政策: 勤政爱民可提声望, 任用贤能可增威权, 但诏令不当会招致反噬。每月限 1 道。',
  },
  {
    icon: Users,
    title: '大臣',
    body: '召对大臣可影响其忠诚度与派系立场。曹操、袁绍、董卓等 200+ 历史人物皆可收为己用或外戚安抚。',
  },
  {
    icon: Sword,
    title: '派系',
    body: '外戚、宦官、世族、寒门、边将 5 大派系此消彼长, 需用联姻、迁都、密令等手段制衡。',
  },
  {
    icon: Sparkles,
    title: '技能',
    body: '献帝可学习 4 系技能 (帝术/用人/军事/民生), 解锁更强的政策选项与被动加成。',
  },
  {
    icon: Building,
    title: '建筑',
    body: '建设宫殿、农田、水利、军营等设施, 提升国势与经济。建筑需要时间与库银, 且受派系阻力。',
  },
]

const SHORTCUT_LIST: { keys: string; desc: string }[] = [
  { keys: '1-9', desc: '切换前 9 个 Tab' },
  { keys: 'L', desc: '日志 Tab' },
  { keys: 'C', desc: '后宫 Tab' },
  { keys: 'S', desc: '弹 国势详情 弹窗' },
  { keys: 'H', desc: '弹 回合历史 弹窗' },
  { keys: 'E', desc: '弹 提取透明 弹窗' },
  { keys: '?', desc: '弹 帮助 (本弹窗)' },
  { keys: 'Esc', desc: '关闭弹窗 / 游戏中返回主菜单' },
  { keys: 'Ctrl+`', desc: '工程师控制台 (cheat)' },
]

const CREDITS = [
  { role: '灵感', who: '陈舜臣《三国》/ 罗贯中《三国演义》/ v5.1 内部设计 汉末汉献帝' },
  { role: '技术栈', who: 'Python 3.11 + Flask 3.1 + React 19 + Vite 5 + TypeScript 5' },
  { role: 'LLM', who: 'MiniMax-Text-01 / deepseek-v4-flash (OpenAI SDK 2.38 兼容)' },
  { role: 'AI 生图', who: 'MiniMax image-01 (v5.2.0+ AI 贴图)' },
  { role: '开发', who: '主公 + AI 协程' },
]

export function HelpModal({ open, onClose }: HelpModalProps) {
  const [tab, setTab] = useState<Tab>('play')

  useEffect(() => {
    if (!open) return
    setTab('play')
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '720px', maxHeight: '85vh' }}>
        <div className="modal__title">帮助</div>

        {/* 3 Tab 切换 */}
        <div className="help-tabs">
          <button
            type="button"
            className={`help-tab ${tab === 'play' ? 'help-tab--active' : ''}`}
            onClick={() => setTab('play')}
          >
            <BookOpen size={14} /> 玩法
          </button>
          <button
            type="button"
            className={`help-tab ${tab === 'shortcuts' ? 'help-tab--active' : ''}`}
            onClick={() => setTab('shortcuts')}
          >
            <Keyboard size={14} /> 快捷键
          </button>
          <button
            type="button"
            className={`help-tab ${tab === 'credits' ? 'help-tab--active' : ''}`}
            onClick={() => setTab('credits')}
          >
            <Heart size={14} /> 致谢
          </button>
        </div>

        <div className="help-body">
          {tab === 'play' && (
            <div className="help-section">
              {GAMEPLAY_SECTIONS.map((s, i) => {
                const Icon = s.icon
                return (
                  <div key={i} className="help-section__item">
                    <div className="help-section__icon">
                      <Icon size={20} />
                    </div>
                    <div>
                      <h4>{s.title}</h4>
                      <p>{s.body}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {tab === 'shortcuts' && (
            <div className="help-section">
              <table className="help-shortcut-table">
                <tbody>
                  {SHORTCUT_LIST.map(s => (
                    <tr key={s.keys}>
                      <td><kbd className="help-kbd">{s.keys}</kbd></td>
                      <td>{s.desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {tab === 'credits' && (
            <div className="help-section">
              {CREDITS.map((c, i) => (
                <div key={i} className="help-credit-row">
                  <span className="help-credit-role">{c.role}</span>
                  <span className="help-credit-who">{c.who}</span>
                </div>
              ))}
              <div className="help-thanks">
                <p>
                  <b>献给主公</b>: 愿主公在这汉末乱局中, 步步为营, 重振汉室。
                </p>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>
                  v5.2.0 · 2026-06 · https://github.com/lz2026km/han-empire
                </p>
              </div>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '14px' }}>
          <button type="button" className="btn btn--primary" onClick={onClose}>关闭</button>
        </div>
      </div>
    </div>
  )
}
