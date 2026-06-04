/* =============================================
   App.tsx - Main Application Component
   汉献帝之末路 - React Frontend
   ============================================= */
import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { Header } from './components/Header'
import { useGame } from './hooks/useGame'
// v2.0.0 Phase 3.2: useSettlement 抽自 App.tsx:131-184 (55 行)
import { useSettlement } from './hooks/useSettlement'
// v2.0.0 Phase 3.3: useChatModal + useCheatConsole 抽自 App.tsx:86-113 (28 行)
import { useChatModal, useCheatConsole } from './hooks/useChatModal'
// v2.1.0 Phase 3.2: 全局快捷键 (1-9 切 Tab / Ctrl+` cheat / Space 推演)
import { useKeyboard } from './hooks/useKeyboard'
// v2.1.0 Phase 3.2: 主题 (暗/亮 + 4 季节)
import { useTheme } from './hooks/useTheme'
import { MinisterChat } from './components/MinisterChat'
import { EmperorPanel } from './components/EmperorPanel'
import { SceneTransition } from './components/SceneTransition'
import { ChatModal } from './components/ChatModal'
import { EdictModal } from './components/EdictModal'
// v5.0 P0-3: Token 实时仪表盘
import { TokenStatsWidget } from './components/TokenStatsWidget'
import { SettlementLock } from './components/SettlementLock'
import { ReportModal } from './components/ReportModal'
import { ClosedIssuesModal } from './components/ClosedIssuesModal'
import { HistoryModal } from './components/HistoryModal'
import { ExtractionModal } from './components/ExtractionModal'
// v5.2.0 P6-2: 国势详情弹窗 (StateModal)
import { StateModal } from './components/StateModal'
// v5.2.0 P6-5: 通用确认弹窗 (ConfirmDialog)
import { ConfirmDialog } from './components/ConfirmDialog'
// v5.2.0 P6-6: 全屏推演 Loading (LoadingScreen, 替代裸 SettlementLock 显示)
import { LoadingScreen } from './components/LoadingScreen'
// v5.2.0 P6-7: 设置弹窗 (SettingsModal)
import { SettingsModal } from './components/SettingsModal'
// v5.2.0 P6-8: 多周目统计弹窗 (StatsModal)
import { StatsModal } from './components/StatsModal'
// v5.2.0 P6-9: 帮助弹窗 (HelpModal)
import { HelpModal } from './components/HelpModal'
// v5.2.0 P6-13: 9 Tab 顶部 hero 贴图 (TabHero)
import { TabHero } from './components/TabHero'
import { SecretOrdersModal } from './components/SecretOrdersModal'
import { CheatConsole } from './components/CheatConsole'
import { GrandMap } from './components/GrandMap'
// v2.0.0 Phase 3: 抽 9 Tab 后 type {GameState/MinisterStats/FactionStats/Minister} 不再需要
import type { SecretOrder } from './api'
import { api } from './api'
// v2.0.0 Phase 3: 抽 9 Tab 后 CourtLayout/MinisterPortrait/ProvinceMap/BattleView/FactionRelationDiagram 不再直接用
import { ConsortTab } from './components/ConsortTab'
// v5.2.0 P6-1: MenuPage 主菜单 (替代 WelcomeScreen)
import { MenuPage } from './components/MenuPage'
// v2.0.0 Phase 3.1: 9 个 Tab 抽到独立文件
import { OverviewTab } from './components/tabs/OverviewTab'
import { DecreeTab } from './components/tabs/DecreeTab'
import { MinisterTab } from './components/tabs/MinisterTab'
import { FactionTab } from './components/tabs/FactionTab'
import { SkillTab } from './components/tabs/SkillTab'
import { BuildingTab } from './components/tabs/BuildingTab'
import { MapTab } from './components/tabs/MapTab'
import { OrdersTab } from './components/tabs/OrdersTab'
import { LogTab } from './components/tabs/LogTab'
import './styles/app.css'

type Tab = 'overview' | 'decree' | 'ministers' | 'factions' | 'skills' | 'buildings' | 'log' | 'chat' | 'map' | 'orders' | 'consort'

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  // v5.2.0 P6-1: New Game 流程整合到 MenuPage, 不再需要内联 modal
  // (Header "新朝" 按钮改为 returnToMenu 走 MenuPage)

  // Modal states (showSettlement/settlementStages/currentSettlementStage 抽到 useSettlement)
  const [showEdictModal, setShowEdictModal] = useState(false)
  const [showSecretOrders, setShowSecretOrders] = useState(false)
  const [showGrandMap, setShowGrandMap] = useState(false)
  const [secretOrders, setSecretOrders] = useState<SecretOrder[]>([])
  // v5.1.1 P1-3: 月初邸报弹窗
  const [showReportModal, setShowReportModal] = useState(false)
  const [latestGazette, setLatestGazette] = useState<any>(null)
  const [lastGazetteTurn, setLastGazetteTurn] = useState<number>(-1)

  // v5.1.2 P2-1: 关案弹窗
  const [showClosedModal, setShowClosedModal] = useState(false)
  const [closedIssues, setClosedIssues] = useState<any[]>([])
  const [lastClosedTurn, setLastClosedTurn] = useState<number>(-1)

  // v5.1.2 P2-2: HistoryModal 手动触发 (按 H 键)
  const [showHistoryModal, setShowHistoryModal] = useState(false)
  const [historyData, setHistoryData] = useState<any>(null)

  // v5.1.2 P2-3: ExtractionModal 手动触发 (按 E 键)
  const [showExtractionModal, setShowExtractionModal] = useState(false)
  const [extractionData, setExtractionData] = useState<any>(null)

  // v5.2.0 P6-2: 国势详情弹窗 (按 S 键 / OverviewTab 按钮)
  const [showStateModal, setShowStateModal] = useState(false)
  // v5.2.0 P6-4: Header 4 入口对应 Modal state (Settings/Help 在 6.7/6.9 实现)
  const [showSettingsModal, setShowSettingsModal] = useState(false)
  const [showHelpModal, setShowHelpModal] = useState(false)
  // v5.2.0 P6-5: 返回主菜单 二次确认
  const [showReturnConfirm, setShowReturnConfirm] = useState(false)
  // v5.2.0 P6-8: 多周目统计 (从 SettingsModal 嵌套打开)
  const [showStatsModal, setShowStatsModal] = useState(false)

  // v5.3.0 P7-fix: 必须在 useEffect 之前调 useGame(), 否则 TDZ 死区
  const {
    campaignId, gameState, ministers, factions, loading, error, log,
    createCampaign, loadCampaign, saveGame, issueDecree, nextTurn, returnToMenu
  } = useGame()

  // v5.3.0 P7-fix: tabs 必须提到 useMemo 之前, 否则 TDZ
  const tabs: { id: Tab;
  label: string; key: string }[] = [
    { id: 'overview', label: '总览 总览', key: '1' },
    { id: 'decree', label: '诏书 诏书', key: '2' },
    { id: 'chat', label: '召对 召对', key: '3' },
    { id: 'ministers', label: '大臣 大臣', key: '4' },
    { id: 'factions', label: '战斗️ 派系', key: '5' },
    { id: 'skills', label: '技能 技能', key: '6' },
    { id: 'buildings', label: '建筑️ 建筑', key: '7' },
    { id: 'map', label: '地图️ 地图', key: '8' },
    { id: 'orders', label: '密令 密令', key: '9' },
    { id: 'log', label: '列表 日志', key: 'L' },
    { id: 'consort', label: '后宫 后宫', key: 'C' },
  ]

  // v5.3.0 P7-fix: 全部 hooks 必须上移到 useEffect 之前 (避免 TDZ)
  const {
    showChatModal,
    setShowChatModal,
    selectedMinister,
    handleMinisterSelect,
    handleSendMessage,
  } = useChatModal(campaignId, ministers)

  const {
    showCheatConsole,
    setShowCheatConsole,
    handleExecuteCheat,
  } = useCheatConsole(campaignId)

  const { theme, setTheme, cycleSeason, season } = useTheme()

  // v5.1.1 P1-3: 检测 gameState.turn 变化 → 拉 /api/gazette → 弹 ReportModal
  useEffect(() => {
    const currentTurn = gameState?.turn
    if (!campaignId || currentTurn === undefined || currentTurn === null) return
    if (currentTurn === lastGazetteTurn) return  // 已弹过
    api.getGazette(campaignId).then((res) => {
      const g = res?.gazette
      if (!g) return
      // 跳过登基伊始 (turn=0 或 summary 以其开头)
      if (g.turn === 0) return
      if (g.report && g.report.trim().startsWith('登基伊始')) return
      setLatestGazette(g)
      setLastGazetteTurn(currentTurn)
      setShowReportModal(true)
    }).catch(() => {/* 静默 */})
  }, [gameState?.turn, campaignId, lastGazetteTurn])

  // v5.1.2 P2-1: 检测 gameState.turn 变化 → 拉 /api/issues/closed → 弹 ClosedIssuesModal
  useEffect(() => {
    const currentTurn = gameState?.turn
    if (!campaignId || currentTurn === undefined || currentTurn === null) return
    if (currentTurn === lastClosedTurn) return  // 已弹过
    api.getClosedIssues(campaignId, currentTurn).then((res) => {
      const items = res?.issues || []
      setLastClosedTurn(currentTurn)
      if (items.length > 0) {
        setClosedIssues(items)
        // 延迟 600ms, 让 ReportModal 先弹
        setTimeout(() => setShowClosedModal(true), 600)
      }
    }).catch(() => {/* 静默 */})
  }, [gameState?.turn, campaignId, lastClosedTurn])

  // v5.1.2 P2-2: H 键弹 HistoryModal
  useEffect(() => {
    if (!campaignId) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'h' || e.key === 'H') {
        if (showHistoryModal) return
        api.getHistory(campaignId, 20).then((d) => {
          setHistoryData(d)
          setShowHistoryModal(true)
        }).catch(() => {/* 静默 */})
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [campaignId, showHistoryModal])

  // v5.1.2 P2-3: E 键弹 ExtractionModal
  useEffect(() => {
    if (!campaignId) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'e' || e.key === 'E') {
        if (showExtractionModal) return
        api.getExtraction(campaignId).then((d) => {
          setExtractionData(d)
          setShowExtractionModal(true)
        }).catch(() => {/* 静默 */})
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [campaignId, showExtractionModal])

  // v5.2.0 P6-2: S 键弹 StateModal (国势详情)
  useEffect(() => {
    if (!campaignId) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 's' || e.key === 'S') {
        // 不在 input/textarea 中触发
        const tgt = e.target as HTMLElement
        if (tgt && (tgt.tagName === 'INPUT' || tgt.tagName === 'TEXTAREA')) return
        setShowStateModal((v) => !v)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [campaignId])

  // v5.2.0 P6-4: ? 键弹 HelpModal / Esc 游戏中弹返回主菜单确认 (P6-5)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tgt = e.target as HTMLElement
      const inInput = tgt && (tgt.tagName === 'INPUT' || tgt.tagName === 'TEXTAREA')
      if (e.key === '?' && !inInput) {
        setShowHelpModal(true)
        return
      }
      if (e.key === 'Escape' && campaignId && !showStateModal && !showHistoryModal
          && !showExtractionModal && !showReportModal && !showClosedModal
          && !showEdictModal && !showChatModal && !showCheatConsole
          && !showSecretOrders && !showGrandMap && !showSettingsModal
          && !showHelpModal && !showReturnConfirm && !inInput) {
        // Esc 在游戏中 → 弹返回主菜单确认 (v5.2.0 P6-5 ConfirmDialog)
        setShowReturnConfirm(true)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [campaignId, showStateModal, showHistoryModal, showExtractionModal,
      showReportModal, showClosedModal, showEdictModal, showChatModal, showCheatConsole,
      showSecretOrders, showGrandMap, showSettingsModal, showHelpModal, showReturnConfirm])

  // v5.3.0 P7-fix: 删重复的 useChatModal/useCheatConsole/useTheme (已上移 line 133-141)

  // v2.1.0 Phase 3.2: 全局快捷键
  // 1-9 → 切前 9 Tab, Ctrl+` → cheat, Space → 推演, T → 切主题, S → 切季节
  const keyboardShortcuts = useMemo(() => {
    const map: Record<string, (e: KeyboardEvent) => void> = {}
    const tabKeys = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
    tabKeys.forEach((k, i) => {
      if (i < tabs.length) {
        map[k] = () => setActiveTab(tabs[i].id)
      }
    })
    return map
  }, [])
  useKeyboard(keyboardShortcuts, !!campaignId)

  // v5.2.0 P6-1: MenuPage handlers
  const handleMenuNewGame = useCallback(async (emperorName: string) => {
    await createCampaign(emperorName, [])
  }, [createCampaign])

  const handleMenuLoad = useCallback(async (cid: string) => {
    await loadCampaign(cid)
  }, [campaignId]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleMenuContinue = useCallback(async (cid: string) => {
    await loadCampaign(cid)
  }, [campaignId]) // eslint-disable-line react-hooks/exhaustive-deps

  // v2.0.0 Phase 3.3: handleMinisterSelect/handleSendMessage/handleExecuteCheat 已抽到 hook
  // v2.0.0 P0-B3: useCallback 稳定引用，避免 OrdersTab useEffect 死循环
  const handleRefreshSecretOrders = useCallback(() => {
    if (campaignId) {
      api.getSecretOrders(campaignId).then(r => setSecretOrders(r.orders || []))
    }
  }, [campaignId])

  // v2.0.0 Phase 3.2: handleStreamSettlement + eventSourceRef cleanup 已抽到 useSettlement hook
  const {
    showSettlement,
    setShowSettlement,
    settlementStages,
    currentSettlementStage,
    startSettlement: handleStreamSettlement,
  } = useSettlement(campaignId)

  // v2.2.0: EdictModal 自带 SSE 流式颁诏, 旧的 handleEdictPublish 已被取代 (此处不再保留)

  return (
    <div className="app">
      <Header
        gameState={gameState}
        onSave={saveGame}
        onReturnToMenu={campaignId ? () => setShowReturnConfirm(true) : returnToMenu}
        onOpenStateModal={() => setShowStateModal(true)}
        onOpenSettingsModal={() => setShowSettingsModal(true)}
        onOpenHelpModal={() => setShowHelpModal(true)}
        theme={theme}
        season={season}
        onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        onCycleSeason={cycleSeason}
      />

      <main className="app-main">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar__section">
            <div className="sidebar__section-title">导航</div>
            {tabs.map(tab => (
              <div
                key={tab.id}
                className={`sidebar__item ${activeTab === tab.id ? 'sidebar__item--active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
                data-tooltip={`按 <kbd>${tab.key}</kbd> 切换`}
              >
                <span className={`tab-icon tab-icon--${tab.id}`} aria-label={tab.label} />
                <span className="sidebar__item-label">{tab.label}</span>
                <kbd className="sidebar__item-kbd">{tab.key}</kbd>
              </div>
            ))}
          </div>

          {!campaignId && (
            <div className="sidebar__section">
              <div className="sidebar__section-title">快速开始</div>
              <div className="sidebar__item" onClick={() => setShowNewGameModal(true)} role="button" tabIndex={0}>
                + 新建朝代
              </div>
            </div>
          )}
        </aside>

        {/* Content */}
        <div className="content">
          {!campaignId ? (
            // v5.2.0 P6-1: MenuPage 替代 WelcomeScreen (含建新朝/存档列表/LLM 状态)
            <MenuPage
              onNewGame={handleMenuNewGame}
              onLoadSave={handleMenuLoad}
              onContinue={handleMenuContinue}
            />
          ) : (
            <>
              <div className="tabs">
                {tabs.map(tab => (
                  <div
                    key={tab.id}
                    className={`tab ${activeTab === tab.id ? 'tab--active' : ''}`}
                    onClick={() => setActiveTab(tab.id)}
                    data-tooltip={`快捷键 ${tab.key}`}
                  >
                    {tab.label}
                    <kbd className="tab__kbd">{tab.key}</kbd>
                  </div>
                ))}
              </div>

              {/* v5.2.0 P6-13: 当前 Tab 的 hero 贴图 */}
              <TabHero tabId={activeTab} />

              <SceneTransition key={activeTab} type="fade" duration={400}>
                {activeTab === 'overview' && (
                  <OverviewTab gameState={gameState} ministers={ministers} factions={factions} onNextTurn={handleStreamSettlement} onSave={saveGame} onOpenStateModal={() => setShowStateModal(true)} />
                )}
                {activeTab === 'decree' && (
                  <DecreeTab gameState={gameState} ministers={ministers} onIssue={issueDecree} />
                )}
                {activeTab === 'chat' && campaignId && (
                  <MinisterChat campaignId={campaignId} ministers={ministers} onMinisterSelect={handleMinisterSelect} />
                )}
                {activeTab === 'ministers' && (
                  <MinisterTab ministers={ministers} />
                )}
                {activeTab === 'factions' && (
                  <FactionTab factions={factions} />
                )}
                {activeTab === 'skills' && (
                  <SkillTab campaignId={campaignId} />
                )}
                {activeTab === 'buildings' && (
                  <BuildingTab campaignId={campaignId} />
                )}
                {activeTab === 'map' && campaignId && (
                  <MapTab />
                )}
                {activeTab === 'orders' && campaignId && (
                  // v2.0.0 P0-B3: useCallback 稳定引用，避免 OrdersTab useEffect 死循环
                  <OrdersTab key={campaignId} secretOrders={secretOrders} onRefresh={handleRefreshSecretOrders} />
                )}
                {activeTab === 'log' && (
                  <LogTab entries={log} />
                )}
                {activeTab === 'consort' && campaignId && (
                  <ConsortTab campaignId={campaignId} />
                )}
              </SceneTransition>
            </>
          )}
        </div>

        {/* Right sidebar - Emperor Panel */}
        {campaignId && (
          <aside className="emperor-sidebar">
            <EmperorPanel gameState={gameState} />
          </aside>
        )}
      </main>

      {/* v5.2.0 P6-1: 内联 New Game Modal 已删除, 整合到 MenuPage */}

      {error && (
        <div className="modal-overlay" onClick={() => {}}>
          <div className="modal">
            <div className="modal__title">[警告]️ 错误</div>
            <p style={{ color: 'var(--color-accent-red-bright)' }}>{error}</p>
            <button type="button" className="btn" onClick={() => window.location.reload()} style={{ marginTop: '16px' }}>刷新</button>
          </div>
        </div>
      )}

      {/* Chat Modal */}
      <ChatModal
        isOpen={showChatModal}
        onClose={() => setShowChatModal(false)}
        campaignId={campaignId || ''}
        minister={selectedMinister}
        onSendMessage={handleSendMessage}
      />

      {/* Edict Modal - v2.2.0 内部设计: 3 阶段 (草稿池/拟诏/颁布 SSE 流式) */}
      <EdictModal
        isOpen={showEdictModal}
        onClose={() => setShowEdictModal(false)}
        campaignId={gameState?.campaign_id || ''}
      />

      {/* Settlement Lock Modal - v2.2.0 内部设计: 全屏锁 + 3 态推演 */}
      <SettlementLock
        stage=""
        thinking=""
        narrative=""
        done={!showSettlement}
        onClose={() => setShowSettlement(false)}
        {...(showSettlement ? {
          stage: (settlementStages.find(s => s.id === currentSettlementStage)?.name) || '推演中',
          thinking: '主公稍候...',
        } : {})}
      />

      {/* Secret Orders Modal */}
      <SecretOrdersModal
        isOpen={showSecretOrders}
        onClose={() => setShowSecretOrders(false)}
        orders={secretOrders}
        onCancelOrder={(orderId) => {
          if (campaignId) {
            api.cancelSecretOrder(campaignId, orderId).then(() => {
              // v2.0.0 P0-B6: cancelSecretOrder 返回 { message }，不应取 r.orders
              api.getSecretOrders(campaignId).then(r => setSecretOrders(r.orders || []))
            })
          }
        }}
      />

      {/* Cheat Console (v4.6 工程师控制台) */}
      <CheatConsole
        isOpen={showCheatConsole}
        onClose={() => setShowCheatConsole(false)}
        onExecuteCommand={handleExecuteCheat}
        campaignId={campaignId}
      />

      {/* v5.1.1 P1-3: 月初邸报弹窗 */}
      <ReportModal
        open={showReportModal}
        gazette={latestGazette}
        onClose={() => setShowReportModal(false)}
      />

      {/* v5.1.2 P2-1: 关案弹窗 */}
      <ClosedIssuesModal
        open={showClosedModal}
        issues={closedIssues}
        onClose={() => setShowClosedModal(false)}
      />

      {/* v5.1.2 P2-2: 回合历史 (H 键触发) */}
      <HistoryModal
        open={showHistoryModal}
        data={historyData}
        onClose={() => setShowHistoryModal(false)}
      />

      {/* v5.1.2 P2-3: 提取透明 (E 键触发) */}
      <ExtractionModal
        open={showExtractionModal}
        data={extractionData}
        onClose={() => setShowExtractionModal(false)}
      />

      {/* v5.2.0 P6-2: 国势详情 (S 键触发 / OverviewTab 按钮) */}
      <StateModal
        open={showStateModal}
        gameState={gameState}
        ministers={ministers}
        factions={factions}
        onClose={() => setShowStateModal(false)}
      />

      {/* v5.2.0 P6-5: 返回主菜单 二次确认 */}
      <ConfirmDialog
        open={showReturnConfirm}
        title="返回主菜单?"
        body="当前对局将保留在存档中, 你可以稍后从主菜单继续。如想彻底重新开始, 请在主菜单选'建立新朝'。"
        confirmText="返回主菜单"
        cancelText="继续游戏"
        variant="warning"
        onConfirm={() => {
          setShowReturnConfirm(false)
          returnToMenu()
        }}
        onCancel={() => setShowReturnConfirm(false)}
      />

      {/* v5.2.0 P6-4: 设置 Modal (6.7 实现) */}
      <SettingsModal
        open={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        onOpenStats={() => setShowStatsModal(true)}
      />

      {/* v5.2.0 P6-8: 多周目统计 (从 SettingsModal 打开) */}
      <StatsModal
        open={showStatsModal}
        onClose={() => setShowStatsModal(false)}
      />

      {/* v5.2.0 P6-4: 帮助 Modal (6.9 实现) */}
      <HelpModal
        open={showHelpModal}
        onClose={() => setShowHelpModal(false)}
      />

      {/* Grand Map */}
      {/* v2.0.0 P0-B2: provinces 为空数组时 onProvinceClick 应可空调用 */}
      <GrandMap
        isOpen={showGrandMap}
        onClose={() => setShowGrandMap(false)}
        provinces={[]}
        onProvinceClick={(id) => { console.log('v2.0.0 P0-B2 选中州郡', id) }}
      />

      {/* v5.2.0 P6-6 + v5.3.0 P7-1: 全局推演 Loading (阶段联动) */}
      <LoadingScreen
        open={loading && !!campaignId}
        title={showSettlement ? '推演下月' : '处理中'}
        currentStage={showSettlement ? currentSettlementStage : undefined}
      />

      {/* v5.0 P0-3: Token 实时仪表盘 (右上角悬浮) */}
      <TokenStatsWidget refreshIntervalSec={30} />
    </div>
  )
}

// ---- Sub-components ----

// v5.2.0 P6-1: WelcomeScreen 已删除, 整合到 MenuPage

// v2.0.0 Phase 3.1: getAuthorityTier 已迁到 components/tabs/OverviewTab.tsx
