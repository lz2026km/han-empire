/* =============================================
   BottomNav - 底部主导航 (v5.4.0 P7-A5)
   4 大图标 + 主菜单/设置/帮助 辅助入口
   ============================================= */
import { Swords, ScrollText, Edit3, BookOpen, Menu, Settings, HelpCircle, Power } from 'lucide-react'

interface BottomNavProps {
  onMenuClick?: () => void
  onSettingsClick?: () => void
  onHelpClick?: () => void
  onReturnToMenu?: () => void
  onQuickPlay?: () => void
}

export function BottomNav({ onMenuClick, onSettingsClick, onHelpClick, onReturnToMenu, onQuickPlay }: BottomNavProps) {
  return (
    <nav className="bottom-nav" role="navigation" aria-label="主导航">
      <button type="button" className="bottom-nav__btn" onClick={onQuickPlay} aria-label="推演下月">
        <Swords size={28} />
        <span className="bottom-nav__label">秦威<br /><small>推演下月</small></span>
      </button>

      <button type="button" className="bottom-nav__btn" aria-label="月初邸报">
        <ScrollText size={28} />
        <span className="bottom-nav__label">邸报详明<br /><small>月初奏章</small></span>
      </button>

      <button type="button" className="bottom-nav__btn" aria-label="颁诏">
        <Edit3 size={28} />
        <span className="bottom-nav__label">诏书草案<br /><small>御笔亲批</small></span>
      </button>

      <button type="button" className="bottom-nav__btn" aria-label="史册">
        <BookOpen size={28} />
        <span className="bottom-nav__label">史册<br /><small>历代奏摺/诏书</small></span>
      </button>

      <div className="bottom-nav__divider" />

      <button type="button" className="bottom-nav__btn bottom-nav__btn--small" onClick={onMenuClick} aria-label="主菜单">
        <Menu size={20} />
        <span className="bottom-nav__label">主菜单</span>
      </button>

      <button type="button" className="bottom-nav__btn bottom-nav__btn--small" onClick={onSettingsClick} aria-label="设置">
        <Settings size={20} />
        <span className="bottom-nav__label">设置</span>
      </button>

      <button type="button" className="bottom-nav__btn bottom-nav__btn--small" onClick={onHelpClick} aria-label="帮助">
        <HelpCircle size={20} />
        <span className="bottom-nav__label">帮助</span>
      </button>

      <button type="button" className="bottom-nav__btn bottom-nav__btn--small bottom-nav__btn--danger" onClick={onReturnToMenu} aria-label="返回主菜单">
        <Power size={20} />
        <span className="bottom-nav__label">返回</span>
      </button>
    </nav>
  )
}
