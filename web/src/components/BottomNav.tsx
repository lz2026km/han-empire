/* =============================================
   BottomNav - 底部主导航 (v5.4.0 P7-A5 + v5.5.0+ P8-G1)
   4 大图标 + 主菜单/设置/帮助 辅助入口 (8 个 btn/ AI 小图)
   ============================================= */

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
        <img className="bottom-nav__icon" src="/btn/btn_play_swords.jpg" alt="" loading="lazy" />
        <span className="bottom-nav__label">秦威<br /><small>推演下月</small></span>
      </button>

      <button type="button" className="bottom-nav__btn" aria-label="月初邸报">
        <img className="bottom-nav__icon" src="/btn/btn_report_scroll.jpg" alt="" loading="lazy" />
        <span className="bottom-nav__label">邸报详明<br /><small>月初奏章</small></span>
      </button>

      <button type="button" className="bottom-nav__btn" aria-label="颁诏">
        <img className="bottom-nav__icon" src="/btn/btn_decree_brush.jpg" alt="" loading="lazy" />
        <span className="bottom-nav__label">诏书草案<br /><small>御笔亲批</small></span>
      </button>

      <button type="button" className="bottom-nav__btn" aria-label="史册">
        <img className="bottom-nav__icon" src="/btn/btn_history_book.jpg" alt="" loading="lazy" />
        <span className="bottom-nav__label">史册<br /><small>历代奏摺/诏书</small></span>
      </button>

      <div className="bottom-nav__divider" />

      <button type="button" className="bottom-nav__btn bottom-nav__btn--small" onClick={onMenuClick} aria-label="主菜单">
        <img className="bottom-nav__icon" src="/btn/btn_menu_grid.jpg" alt="" loading="lazy" />
        <span className="bottom-nav__label">主菜单</span>
      </button>

      <button type="button" className="bottom-nav__btn bottom-nav__btn--small" onClick={onSettingsClick} aria-label="设置">
        <img className="bottom-nav__icon" src="/btn/btn_tts.jpg" alt="" loading="lazy" />
        <span className="bottom-nav__label">设置</span>
      </button>

      <button type="button" className="bottom-nav__btn bottom-nav__btn--small" onClick={onHelpClick} aria-label="帮助">
        <img className="bottom-nav__icon" src="/btn/btn_help_lamp.jpg" alt="" loading="lazy" />
        <span className="bottom-nav__label">帮助</span>
      </button>

      <button type="button" className="bottom-nav__btn bottom-nav__btn--small bottom-nav__btn--danger" onClick={onReturnToMenu} aria-label="返回主菜单">
        <img className="bottom-nav__icon" src="/btn/btn_danger.jpg" alt="" loading="lazy" />
        <span className="bottom-nav__label">返回</span>
      </button>
    </nav>
  )
}
