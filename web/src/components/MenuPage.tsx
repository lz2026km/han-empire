/* =============================================
   MenuPage - 主菜单页 (v5.1.4 P4-1)
   v5.1 内部设计 MenuPage, 选项: 继续/新朝/读档/退出
   v5.2.0 P6-3: 改用 NewGameModal 组件
   v5.2.0 P6-12: 美化 (主公头像 + 朝代 banner + 4 季节背景)
   ============================================= */
import { useEffect, useState } from 'react'
import { Crown, Save, Plus, Power, Key, Folder, Trash2 } from 'lucide-react'
import { api } from '../api'
import { NewGameModal } from './NewGameModal'
import { useTheme } from '../hooks/useTheme'

interface Save {
  campaign_id: string
  filename: string
  size: number
  mtime: number
}

interface MenuStatus {
  saves: Save[]
  total_saves: number
  has_api_key: boolean
  has_running_game: boolean
  llm: { has_api_key: boolean; model: string; base_url: string }
  version: string
}

interface MenuPageProps {
  onNewGame: (emperorName?: string) => void | Promise<void>
  onLoadSave: (saveId: string) => void | Promise<void>
  onContinue: (saveId: string) => void | Promise<void>
  onShutdown?: () => void
}

export function MenuPage({ onNewGame, onLoadSave, onContinue, onShutdown }: MenuPageProps) {
  const [status, setStatus] = useState<MenuStatus | null>(null)
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  // v5.2.0 P6-3: 建新朝用 NewGameModal 弹窗 (替代原内联 input + button)
  const [showNewGameModal, setShowNewGameModal] = useState(false)
  // v5.2.0 P6-12: 季节背景 (随 useTheme 切换)
  const { season } = useTheme()

  useEffect(() => {
    refresh()
  }, [])

  const refresh = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await api.getMenuStatus()
      setStatus(data)
    } catch (e: any) {
      setError(e?.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleNewGame = async (name: string) => {
    setBusy(true)
    setError('')
    try {
      await onNewGame(name)
      setShowNewGameModal(false)
    } catch (e: any) {
      setError(e?.message || '建立新朝失败')
    } finally {
      setBusy(false)
    }
  }

  const handleLoad = async (saveId: string) => {
    setBusy(true)
    setError('')
    try {
      await onLoadSave(saveId)
    } catch (e: any) {
      setError(e?.message || '读档失败')
    } finally {
      setBusy(false)
    }
  }

  const handleContinue = async (saveId: string) => {
    setBusy(true)
    setError('')
    try {
      await onContinue(saveId)
    } catch (e: any) {
      setError(e?.message || '继续失败')
    } finally {
      setBusy(false)
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  const formatTime = (mtime: number) => {
    try {
      return new Date(mtime * 1000).toLocaleString('zh-CN', { hour12: false })
    } catch {
      return ''
    }
  }

  if (loading) {
    return (
      <div className="menu-page">
        <div className="menu-page__loading">加载菜单状态中...</div>
      </div>
    )
  }

  return (
    <div className="menu-page" data-season={season}>
      {/* v5.2.0 P6-12: 朝代 banner 背景 (4 季节, AI 生图) */}
      <div className="menu-page__banner" aria-hidden="true" />
      <div className="menu-page__header">
        {/* v5.2.0 P6-12: 主公头像 (圆形 mask, 金边) */}
        <div className="menu-page__avatar" aria-label="汉献帝刘协">
          <Crown size={48} className="menu-page__avatar-fallback" />
        </div>
        <h1>汉献帝之末路</h1>
        <p className="menu-page__subtitle">献帝 v{status?.version || '5.2.0'} · 回合制汉风政治游戏</p>
      </div>

      {error && <div className="menu-page__error">[X] {error}</div>}

      <div className="menu-page__llm">
        <Key size={16} />
        <span>LLM 配置: </span>
        <span className={status?.has_api_key ? 'menu-page__llm-ok' : 'menu-page__llm-no'}>
          {status?.has_api_key ? '已配置' : '未配置 API Key'}
        </span>
        {status?.llm?.model && (
          <span className="menu-page__llm-meta">
            {status.llm.model} ({status.llm.base_url})
          </span>
        )}
      </div>

      <div className="menu-page__actions">
        <div className="menu-page__action-card">
          <h3>建立新朝</h3>
          <p>以汉献帝身份开始, 在 189-220 年的乱局中求存</p>
          <button
            type="button"
            className="menu-page__btn menu-page__btn--primary"
            onClick={() => setShowNewGameModal(true)}
            disabled={busy}
          >
            <Plus size={16} /> + 建立新朝
          </button>
        </div>

        <div className="menu-page__action-card">
          <h3>存档 ({status?.total_saves || 0})</h3>
          <p>从存档继续游戏 (按时间倒序)</p>
          <div className="menu-page__saves">
            {status?.saves && status.saves.length > 0 ? (
              <ul className="menu-page__save-list">
                {status.saves.slice(0, 10).map((s) => (
                  <li key={s.campaign_id} className="menu-page__save-item">
                    <div className="menu-page__save-info">
                      <div className="menu-page__save-id">
                        <Save size={14} /> {s.campaign_id}
                      </div>
                      <div className="menu-page__save-meta">
                        {formatSize(s.size)} · {formatTime(s.mtime)}
                      </div>
                    </div>
                    <div className="menu-page__save-actions">
                      <button
                        type="button"
                        className="menu-page__btn menu-page__btn--small"
                        onClick={() => handleContinue(s.campaign_id)}
                        disabled={busy}
                        aria-label="继续"
                      >
                        继续
                      </button>
                      <button
                        type="button"
                        className="menu-page__btn menu-page__btn--small"
                        onClick={() => handleLoad(s.campaign_id)}
                        disabled={busy}
                        aria-label="读档"
                      >
                        读档
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="menu-page__no-saves">
                <Folder size={24} />
                <p>暂无存档</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {onShutdown && (
        <div className="menu-page__footer">
          <button
            type="button"
            className="menu-page__btn menu-page__btn--ghost"
            onClick={onShutdown}
            disabled={busy}
          >
            <Power size={14} /> 退出
          </button>
          <button
            type="button"
            className="menu-page__btn menu-page__btn--ghost"
            onClick={refresh}
            disabled={busy}
            aria-label="刷新"
          >
            <Trash2 size={14} /> 刷新
          </button>
        </div>
      )}

      {/* v5.2.0 P6-3: 建新朝弹窗 (从内联 input 抽到组件) */}
      <NewGameModal
        open={showNewGameModal}
        loading={busy}
        onConfirm={handleNewGame}
        onCancel={() => setShowNewGameModal(false)}
      />
    </div>
  )
}
