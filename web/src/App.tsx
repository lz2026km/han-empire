/* =============================================
   App.tsx - Main Application Component
   汉献帝之末路 - React Frontend
   ============================================= */
import { useState, useEffect, useCallback, useRef } from 'react'
import { Header } from './components/Header'
import { useGame } from './hooks/useGame'
// v2.0.0 Phase 3.2: useSettlement 抽自 App.tsx:131-184 (55 行)
import { useSettlement } from './hooks/useSettlement'
// v2.0.0 Phase 3.3: useChatModal + useCheatConsole 抽自 App.tsx:86-113 (28 行)
import { useChatModal, useCheatConsole } from './hooks/useChatModal'
import { MinisterChat } from './components/MinisterChat'
import { EmperorPanel } from './components/EmperorPanel'
import { SceneTransition } from './components/SceneTransition'
import { ChatModal } from './components/ChatModal'
import { EdictModal } from './components/EdictModal'
import { SettlementLock } from './components/SettlementLock'
import { SecretOrdersModal } from './components/SecretOrdersModal'
import { CheatConsole } from './components/CheatConsole'
import { GrandMap } from './components/GrandMap'
// v2.0.0 Phase 3: 抽 9 Tab 后 type {GameState/MinisterStats/FactionStats/Minister} 不再需要
import type { SecretOrder } from './api'
import { api } from './api'
// v2.0.0 Phase 3: 抽 9 Tab 后 CourtLayout/MinisterPortrait/ProvinceMap/BattleView/FactionRelationDiagram 不再直接用
import { ConsortTab } from './components/ConsortTab'
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
  const [showNewGameModal, setShowNewGameModal] = useState(false)
  const [emperorName, setEmperorName] = useState('刘协')

  // Modal states (showSettlement/settlementStages/currentSettlementStage 抽到 useSettlement)
  const [showEdictModal, setShowEdictModal] = useState(false)
  const [showSecretOrders, setShowSecretOrders] = useState(false)
  const [showGrandMap, setShowGrandMap] = useState(false)
  const [secretOrders, setSecretOrders] = useState<SecretOrder[]>([])

  const {
    campaignId, gameState, ministers, factions, loading, error, log,
    createCampaign, saveGame, issueDecree, nextTurn
  } = useGame()

  // v2.0.0 Phase 3.3: 抽 3 个 handleMinister/Send/Cheat 调用到 useChatModal/useCheatConsole
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

  // Cheat console keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === '`') {
        e.preventDefault()
        setShowCheatConsole(prev => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const handleNewGame = async () => {
    setShowNewGameModal(false)
    await createCampaign(emperorName, [])
  }

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

  const handleEdictPublish = useCallback(async (content: string, isSecret: boolean) => {
    if (!campaignId) return
    await issueDecree('edict')
  }, [campaignId, issueDecree])

  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: '🏠 总览' },
    { id: 'decree', label: '📜 诏书' },
    { id: 'chat', label: '💬 召对' },
    { id: 'ministers', label: '👥 大臣' },
    { id: 'factions', label: '⚔️ 派系' },
    { id: 'skills', label: '🌲 技能' },
    { id: 'buildings', label: '🏛️ 建筑' },
    { id: 'map', label: '🗺️ 地图' },
    { id: 'orders', label: '🔐 密令' },
    { id: 'log', label: '📋 日志' },
    { id: 'consort', label: '🏯 后宫' },
  ]

  return (
    <div className="app">
      <Header
        gameState={gameState}
        onSave={saveGame}
        onNewGame={() => setShowNewGameModal(true)}
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
              >
                {tab.label}
              </div>
            ))}
          </div>

          {!campaignId && (
            <div className="sidebar__section">
              <div className="sidebar__section-title">快速开始</div>
              <div className="sidebar__item" onClick={() => setShowNewGameModal(true)}>
                ➕ 新建朝代
              </div>
            </div>
          )}
        </aside>

        {/* Content */}
        <div className="content">
          {!campaignId ? (
            <WelcomeScreen onNewGame={() => setShowNewGameModal(true)} />
          ) : (
            <>
              <div className="tabs">
                {tabs.map(tab => (
                  <div
                    key={tab.id}
                    className={`tab ${activeTab === tab.id ? 'tab--active' : ''}`}
                    onClick={() => setActiveTab(tab.id)}
                  >
                    {tab.label}
                  </div>
                ))}
              </div>

              <SceneTransition key={activeTab} type="fade" duration={400}>
                {activeTab === 'overview' && (
                  <OverviewTab gameState={gameState} ministers={ministers} factions={factions} onNextTurn={handleStreamSettlement} onSave={saveGame} />
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

      {/* New Game Modal */}
      {showNewGameModal && (
        <div className="modal-overlay" onClick={() => setShowNewGameModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal__title">🏛️ 建立新朝</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '6px', color: 'var(--color-text-secondary)', fontSize: '13px' }}>
                  皇帝名（默认刘协）
                </label>
                <input
                  type="text"
                  value={emperorName}
                  onChange={e => setEmperorName(e.target.value)}
                  style={{ width: '100%' }}
                />
              </div>
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button className="btn" onClick={() => setShowNewGameModal(false)}>取消</button>
                <button className="btn btn--primary" onClick={handleNewGame} disabled={loading}>
                  {loading ? '创建中...' : '建立朝代'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="modal-overlay" onClick={() => {}}>
          <div className="modal">
            <div className="modal__title">⚠️ 错误</div>
            <p style={{ color: 'var(--color-accent-red-bright)' }}>{error}</p>
            <button className="btn" onClick={() => window.location.reload()} style={{ marginTop: '16px' }}>刷新</button>
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

      {/* Edict Modal */}
      <EdictModal
        isOpen={showEdictModal}
        onClose={() => setShowEdictModal(false)}
        onPublish={handleEdictPublish}
        edictTypes={[
          { id: 'edict', name: '颁布政令', description: '提升威权，降低忠诚', authorityCost: 6 },
          { id: 'appoint', name: '任命诏书', description: '任命大臣，提升忠诚', authorityCost: 5 },
          { id: 'dismiss', name: '贬谪诏书', description: '贬谪大臣，降低其威权', authorityCost: 8 },
          { id: 'inspect', name: '巡视州郡', description: '提升威权，降低派系影响', authorityCost: 3 },
          { id: 'recruit', name: '招贤纳士', description: '随机获得大臣', authorityCost: 10 },
          { id: 'grant', name: '封赏功臣', description: '提升大臣忠诚，降低威权', authorityCost: 7 },
        ]}
      />

      {/* Settlement Lock Modal */}
      <SettlementLock
        isOpen={showSettlement}
        onClose={() => setShowSettlement(false)}
        month={gameState?.month || 1}
        year={gameState?.year || 189}
        stages={settlementStages.map(s => ({ id: s.id, name: s.name, status: s.status as any }))}
        currentStage={currentSettlementStage}
        onStageComplete={(stageId) => { console.log('v2.0.0 P0-B2 阶段完成', stageId) }}
        changes={{}}
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

      {/* Cheat Console */}
      <CheatConsole
        isOpen={showCheatConsole}
        onClose={() => setShowCheatConsole(false)}
        onExecuteCommand={handleExecuteCheat}
      />

      {/* Grand Map */}
      {/* v2.0.0 P0-B2: provinces 为空数组时 onProvinceClick 应可空调用 */}
      <GrandMap
        isOpen={showGrandMap}
        onClose={() => setShowGrandMap(false)}
        provinces={[]}
        onProvinceClick={(id) => { console.log('v2.0.0 P0-B2 选中州郡', id) }}
      />
    </div>
  )
}

// ---- Sub-components ----

function WelcomeScreen({ onNewGame }: { onNewGame: () => void }) {
  return (
    <div className="empty-state" style={{ paddingTop: '80px' }}>
      <div style={{ fontSize: '48px', marginBottom: '20px' }}>⚔️</div>
      <h2 style={{ color: 'var(--color-gold)', marginBottom: '12px', fontSize: '22px' }}>汉献帝之末路</h2>
      <p style={{ marginBottom: '30px', maxWidth: '400px', lineHeight: '1.7' }}>
        你是汉献帝刘协，在董卓、李傕、郭汜的阴影下苟延残喘。
        通过诏书、派系、技能和建筑，一步步夺回皇权。
      </p>
      <button className="btn btn--primary" onClick={onNewGame}>
        ➕ 建立新朝
      </button>
    </div>
  )
}

// v2.0.0 Phase 3.1: getAuthorityTier 已迁到 components/tabs/OverviewTab.tsx
