/* =============================================
   TabHero - Tab 顶部 hero 贴图 (v5.2.0 P6-13)
   v5.1 内部设计 tab_hero, AI 生图 (scripts/gen_images_v52.py)
   ============================================= */
const TAB_HERO_MAP: Record<string, string> = {
  overview: '/v4-epic/tab_hero_overview.jpg',
  decree: '/v4-epic/tab_hero_decree.jpg',
  chat: '/v4-epic/tab_hero_chat.jpg',
  ministers: '/v4-epic/tab_hero_ministers.jpg',
  factions: '/v4-epic/tab_hero_factions.jpg',
  skills: '/v4-epic/tab_hero_skills.jpg',
  buildings: '/v4-epic/tab_hero_buildings.jpg',
  map: '/v4-epic/tab_hero_map.jpg',
  orders: '/v4-epic/tab_hero_orders.jpg',
}

const TAB_LABEL: Record<string, string> = {
  overview: '总览 · 朝会视角',
  decree: '诏书 · 颁布圣旨',
  chat: '召对 · 君臣密谈',
  ministers: '大臣 · 群臣名录',
  factions: '派系 · 势力版图',
  skills: '技能 · 帝王之术',
  buildings: '建筑 · 城池营造',
  map: '地图 · 十三州郡',
  orders: '密令 · 暗棋布局',
}

interface TabHeroProps {
  tabId: string
}

export function TabHero({ tabId }: TabHeroProps) {
  const bg = TAB_HERO_MAP[tabId]
  const label = TAB_LABEL[tabId] || tabId
  if (!bg) return null
  return (
    <div
      className="tab-hero"
      style={{ backgroundImage: `url('${bg}')` }}
      role="img"
      aria-label={label}
    >
      <div className="tab-hero__overlay">
        <h2 className="tab-hero__title">{label}</h2>
      </div>
    </div>
  )
}
