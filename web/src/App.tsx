/* =============================================
   App.tsx - Main Application Component
   汉献帝之末路 - React Frontend
   ============================================= */
import { useState, useEffect, useCallback, useRef } from 'react'
import { Header } from './components/Header'
import { useGame } from './hooks/useGame'
import { MinisterChat } from './components/MinisterChat'
import { EmperorPanel } from './components/EmperorPanel'
import { SceneTransition } from './components/SceneTransition'
import { ChatModal } from './components/ChatModal'
import { EdictModal } from './components/EdictModal'
import { SettlementLock } from './components/SettlementLock'
import { SecretOrdersModal } from './components/SecretOrdersModal'
import { CheatConsole } from './components/CheatConsole'
import { GrandMap } from './components/GrandMap'
import { ProvinceMap } from './components/ProvinceMap'
import { BattleView } from './components/BattleView'
import { FactionRelationDiagram } from './components/FactionRelationDiagram'
import type { GameState, MinisterStats, FactionStats, Minister } from './types'
import type { SecretOrder } from './api'
import { api } from './api'
import { CourtLayout } from './components/CourtLayout'
import { MinisterPortrait } from './components/MinisterPortrait'
import { ConsortTab } from './components/ConsortTab'
import './styles/app.css'

type Tab = 'overview' | 'decree' | 'ministers' | 'factions' | 'skills' | 'buildings' | 'log' | 'chat' | 'map' | 'orders' | 'consort'

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [showNewGameModal, setShowNewGameModal] = useState(false)
  const [emperorName, setEmperorName] = useState('刘协')

  // Modal states
  const [showChatModal, setShowChatModal] = useState(false)
  const [showEdictModal, setShowEdictModal] = useState(false)
  const [showSettlement, setShowSettlement] = useState(false)
  const [showSecretOrders, setShowSecretOrders] = useState(false)
  const [showCheatConsole, setShowCheatConsole] = useState(false)
  const [showGrandMap, setShowGrandMap] = useState(false)
  const [selectedMinister, setSelectedMinister] = useState<Minister | null>(null)
  const [secretOrders, setSecretOrders] = useState<SecretOrder[]>([])
  const [settlementStages, setSettlementStages] = useState<{ id: string; name: string; status: string }[]>([
    { id: 'fiscal', name: '财政结算', status: 'pending' },
    { id: 'faction', name: '藩镇变化', status: 'pending' },
    { id: 'events', name: '事件触发', status: 'pending' },
    { id: 'narrative', name: '叙事生成', status: 'pending' },
  ])
  const [currentSettlementStage, setCurrentSettlementStage] = useState('fiscal')

  const {
    campaignId, gameState, ministers, factions, loading, error, log,
    createCampaign, saveGame, issueDecree, nextTurn
  } = useGame()

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

  const handleMinisterSelect = useCallback((name: string) => {
    const m = ministers.find(min => min.name === name)
    if (m) {
      setSelectedMinister(m)
      setShowChatModal(true)
    }
  }, [ministers])

  const handleSendMessage = useCallback(async (message: string): Promise<string> => {
    if (!campaignId || !selectedMinister) return '请先选择大臣'
    try {
      const res = await api.chatWithMinister(campaignId, selectedMinister.name, message)
      return res.result || '臣...遵旨。'
    } catch {
      return '臣...有事上奏。（网络异常）'
    }
  }, [campaignId, selectedMinister])

  const handleExecuteCheat = useCallback(async (command: string): Promise<{ success: boolean; output: string }> => {
    if (!campaignId) return { success: false, output: '无活动战役' }
    try {
      const [cmd, ...args] = command.split(' ')
      const res = await api.executeCheat(campaignId, cmd, args.length > 0 ? { args } : undefined)
      return res
    } catch (e: any) {
      return { success: false, output: `执行失败: ${e.message}` }
    }
  }, [campaignId])

  // v2.0.0 P0-B3: useCallback 稳定引用，避免 OrdersTab useEffect 死循环
  const handleRefreshSecretOrders = useCallback(() => {
    if (campaignId) {
      api.getSecretOrders(campaignId).then(r => setSecretOrders(r.orders || []))
    }
  }, [campaignId])

  const eventSourceRef = useRef<EventSource | null>(null)
  // v2.0.0 P0-B4: 组件卸载时关闭 SSE
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [])

  const handleStreamSettlement = useCallback(async () => {
    if (!campaignId) return
    setShowSettlement(true)
    setSettlementStages([
      { id: 'fiscal', name: '财政结算', status: 'pending' },
      { id: 'faction', name: '藩镇变化', status: 'pending' },
      { id: 'events', name: '事件触发', status: 'pending' },
      { id: 'narrative', name: '叙事生成', status: 'pending' },
    ])
    setCurrentSettlementStage('fiscal')

    try {
      // v2.0.0 P0-B4: 用 ref 持有 EventSource 以便 cleanup
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
      const eventSource = api.streamSettlement(campaignId)
      eventSourceRef.current = eventSource

      eventSource.addEventListener('stage', (e) => {
        const data = JSON.parse(e.data)
        if (data.stage === 'thinking') {
          setCurrentSettlementStage(data.stage)
        } else {
          setCurrentSettlementStage(data.stage.replace('_done', ''))
          setSettlementStages(prev => prev.map(s =>
            s.id === data.stage.replace('_done', '') ? { ...s, status: 'done' } : s
          ))
        }
      })

      eventSource.addEventListener('thinking', (e) => {
        // Handle thinking state
      })

      eventSource.addEventListener('text', (e) => {
        // Handle text output
      })

      eventSource.addEventListener('done', () => {
        eventSource.close()
        eventSourceRef.current = null
        setShowSettlement(false)
      })

      eventSource.addEventListener('error', () => {
        eventSource.close()
        eventSourceRef.current = null
        setShowSettlement(false)
      })
    } catch (e) {
      setShowSettlement(false)
    }
  }, [campaignId])

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

function OverviewTab({
  gameState, ministers, factions, onNextTurn, onSave
}: {
  gameState: GameState | null
  ministers: MinisterStats[]
  factions: any[]
  onNextTurn: () => void
  onSave: () => void
}) {
  if (!gameState) return null
  return (
    <div className="fade-in">
      <div className="action-row">
        <button className="btn btn--primary" onClick={onNextTurn}>⏭️ 下一个月</button>
        {/* v2.0.0 P0-B1: 存档按钮接 saveGame */}
        <button className="btn btn--gold" onClick={onSave}>💾 存档</button>
      </div>

      <div className="grid-3" style={{ marginBottom: '20px' }}>
        <div className="card card--gold">
          <div style={{ color: 'var(--color-gold)', fontSize: '13px', marginBottom: '8px' }}>威权值</div>
          <div style={{ fontSize: '36px', color: 'var(--color-gold-bright)', marginBottom: '8px' }}>
            {gameState.emperor_authority}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
            7档: {getAuthorityTier(gameState.emperor_authority)}阶
          </div>
        </div>
        <div className="card">
          <div style={{ color: 'var(--color-text-secondary)', fontSize: '13px', marginBottom: '8px' }}>忠诚度</div>
          <div style={{ fontSize: '36px', color: 'var(--color-text-primary)' }}>
            {gameState.emperor_loyalty}
          </div>
        </div>
        <div className="card">
          <div style={{ color: 'var(--color-text-secondary)', fontSize: '13px', marginBottom: '8px' }}>在册大臣</div>
          <div style={{ fontSize: '36px', color: 'var(--color-text-primary)' }}>
            {ministers.length}
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div style={{ color: 'var(--color-gold)', marginBottom: '12px' }}>派系形势</div>
          {factions.map(f => (
            <div key={f.id} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span>{f.name}</span>
              <span style={{ color: 'var(--color-gold)' }}>{f.influence}</span>
            </div>
          ))}
        </div>
        <div className="card">
          <div style={{ color: 'var(--color-gold)', marginBottom: '12px' }}>近期大臣</div>
          {ministers.slice(0, 5).map(m => (
            <div key={m.id} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span>{m.name}</span>
              <span style={{ color: 'var(--color-text-muted)' }}>{m.faction}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function DecreeTab({
  gameState, ministers, onIssue
}: {
  gameState: GameState | null
  ministers: MinisterStats[]
  onIssue: (decreeType: string, targetId?: number) => void
}) {
  const decreeTypes = gameState?.available_decree_types || []
  return (
    <div className="fade-in">
      <div style={{ marginBottom: '16px', color: 'var(--color-text-secondary)', fontSize: '13px' }}>
        选择诏书类型发布诏令，每种诏书有不同效果和威权消耗。
      </div>
      <div className="decree-grid">
        {decreeTypes.map(dt => (
          <DecreeCard key={dt} decreeType={dt} ministers={ministers} onIssue={onIssue} />
        ))}
      </div>
    </div>
  )
}

function DecreeCard({
  decreeType, onIssue
}: {
  decreeType: string
  ministers: MinisterStats[]
  onIssue: (decreeType: string, targetId?: number) => void
}) {
  const decreeMeta: Record<string, { name: string; effect: string; cost: number }> = {
    appoint: { name: '任命诏书', effect: '任命大臣，提升忠诚', cost: 5 },
    dismiss: { name: '贬谪诏书', effect: '贬谪大臣，降低其威权', cost: 8 },
    inspect: { name: '巡视州郡', effect: '提升威权，降低派系影响', cost: 3 },
    recruit: { name: '招贤纳士', effect: '随机获得大臣', cost: 10 },
    edict: { name: '颁布政令', effect: '提升威权，降低忠诚', cost: 6 },
    grant: { name: '封赏功臣', effect: '提升大臣忠诚，降低威权', cost: 7 },
  }
  const meta = decreeMeta[decreeType] || { name: decreeType, effect: '', cost: 5 }
  return (
    <div className="decree-card">
      <div className="decree-card__name">{meta.name}</div>
      <div className="decree-card__effect">{meta.effect}</div>
      <div className="decree-card__cost">威权消耗: {meta.cost}</div>
      <button
        className="btn btn--primary"
        style={{ marginTop: '10px', width: '100%', fontSize: '12px' }}
        onClick={() => onIssue(decreeType)}
      >
        发布
      </button>
    </div>
  )
}

function MinisterTab({ ministers }: { ministers: MinisterStats[] }) {
  const [courtMode, setCourtMode] = useState<'grid' | 'court'>('grid')

  const handleMinisterClick = (m: MinisterStats) => {
    // TODO: Open chat with minister
    console.log('Selected minister:', m.name)
  }

  const courtMinisters = ministers.map(m => ({
    id: String(m.id),
    name: m.name,
    office: m.position,
    faction: m.faction,
    status: 'active' as const,
    status_label: '在朝',
    summary: `忠诚${m.loyalty} | 能力${m.ability}`,
    portrait_id: m.portrait,
  }))

  return (
    <div className="fade-in">
      <div className="minister-tab-header">
        <div className="minister-tab-tabs">
          <button
            className={`minister-tab-btn ${courtMode === 'grid' ? 'active' : ''}`}
            onClick={() => setCourtMode('grid')}
          >
            网格视图
          </button>
          <button
            className={`minister-tab-btn ${courtMode === 'court' ? 'active' : ''}`}
            onClick={() => setCourtMode('court')}
          >
            朝会视图
          </button>
        </div>
      </div>

      {courtMode === 'grid' ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '12px' }}>
          {ministers.map(m => (
            <div key={m.id} className="minister-card">
              <div className="minister-card-portrait-wrap">
                <MinisterPortrait
                  primary={m.portrait ? `/portraits/minister_${m.id}.png` : undefined}
                  name={m.name}
                  size="medium"
                />
              </div>
              <div className="minister-card__info">
                <div className="minister-card__name">{m.name}</div>
                <div className="minister-card__stats">
                  <span>{m.position}</span>
                  <span className="minister-card__faction" style={{ background: `var(--faction-${m.faction})` }}>
                    {m.faction}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '12px', marginTop: '6px' }}>
                  <div className="minister-stat-bar">
                    <span className="minister-stat-bar__label">忠</span>
                    <div className="minister-stat-bar__track">
                      <div className="minister-stat-bar__fill" style={{ width: `${m.loyalty}%`, background: 'var(--color-gold)' }} />
                    </div>
                  </div>
                  <div className="minister-stat-bar">
                    <span className="minister-stat-bar__label">能</span>
                    <div className="minister-stat-bar__track">
                      <div className="minister-stat-bar__fill" style={{ width: `${m.ability}%`, background: 'var(--color-accent-red)' }} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <CourtLayout
          ministers={courtMinisters}
          selectedMinister=""
          onOpenChat={handleMinisterClick as any}
          courtMode="grid"
        />
      )}
    </div>
  )
}

function FactionTab({ factions }: { factions: FactionStats[] }) {
  const [showDiagram, setShowDiagram] = useState(false)

  const factionNodes = factions.map(f => ({
    id: f.id,
    name: f.name,
    influence: f.influence,
    color: f.color || 'var(--color-gold)',
    ministers: [],
    description: f.description || `${f.name} - 影响力: ${f.influence}`,
  }))

  const mockRelations = [
    { source: 'dong', target: 'cao', type: 'rival' as const, strength: 80 },
    { source: 'yuan', target: 'cao', type: 'rival' as const, strength: 60 },
    { source: 'han', target: 'dong', type: 'alliance' as const, strength: 70 },
    { source: 'han', target: 'cao', type: 'rival' as const, strength: 90 },
  ]

  return (
    <div className="fade-in">
      <div className="faction-tab-header">
        <button
          className={`faction-view-btn ${showDiagram ? 'active' : ''}`}
          onClick={() => setShowDiagram(!showDiagram)}
        >
          {showDiagram ? '返回列表' : '派系关系图'}
        </button>
      </div>

      {showDiagram ? (
        <div className="faction-diagram-container">
          <FactionRelationDiagram
            factions={factionNodes}
            relations={mockRelations}
            width={700}
            height={450}
          />
        </div>
      ) : (
        <div className="faction-panel">
          {factions.map(f => (
            <div key={f.id} className="faction-card">
              <div className="faction-card__header">
                <span className="faction-card__name" style={{ color: f.color || 'var(--color-gold)' }}>
                  {f.name}
                </span>
                <span className="faction-card__influence">{f.influence}</span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                首领: {f.leader_name}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                影响力 {f.influence}，{f.dominant_ministers}名大臣
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function SkillTab({ campaignId }: { campaignId: string }) {
  const [skillTree, setSkillTree] = useState<{
    branches: Record<string, { id: string; name: string; cost: number; tier: number; unlocked: boolean }[]>
    authority_required: number
    skill_points: number
  } | null>(null)
  const [activating, setActivating] = useState<string | null>(null)

  useEffect(() => {
    if (!campaignId) return
    api.getSkillTree(campaignId).then(res => {
      const tree = (res as any).skill_tree
      setSkillTree(tree)
    }).catch(() => {
      setSkillTree({ branches: {}, authority_required: 0, skill_points: 0 })
    })
  }, [campaignId])

  const handleActivate = async (skillId: string) => {
    setActivating(skillId)
    try {
      await api.unlockSkill(campaignId, skillId)
      const res = await api.getSkillTree(campaignId)
      setSkillTree((res as any).skill_tree)
    } catch (e) {
      console.error(e)
    }
    setActivating(null)
  }

  const branches = skillTree?.branches || {}
  const skillPoints = skillTree?.skill_points || 0

  const branchNames: Record<string, string> = {
    'jinglve': '经略',
    'zhengzhi': '权谋',
    'junlu': '武功',
    'wenzhi': '文治',
  }

  return (
    <div className="fade-in">
      <div className="skill-header">
        <div className="skill-points-badge">
          <span className="skill-points-label">技能点</span>
          <span className="skill-points-value">{skillPoints}</span>
        </div>
      </div>

      <div className="skill-branches">
        {Object.entries(branches).map(([branchKey, skills]) => (
          <div key={branchKey} className="skill-branch-card">
            <div className="skill-branch-header">
              <span className="skill-branch-name">{branchNames[branchKey] || branchKey}</span>
              <span className="skill-branch-count">{skills.filter(s => s.unlocked).length}/{skills.length}</span>
            </div>
            <div className="skill-nodes">
              {skills.map(skill => (
                <button
                  key={skill.id}
                  className={`skill-node ${skill.unlocked ? 'skill-node--unlocked' : 'skill-node--locked'}`}
                  onClick={() => !skill.unlocked && handleActivate(skill.id)}
                  disabled={skill.unlocked || activating === skill.id}
                  title={`消耗 ${skill.cost} 点`}
                >
                  <div className="skill-node-name">{skill.name}</div>
                  <div className="skill-node-tier">阶{skill.tier}</div>
                  {skill.unlocked && <div className="skill-node-check">✓</div>}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {Object.keys(branches).length === 0 && (
        <div className="empty-state">
          <p>威权达到40后将解锁技能树</p>
          <p style={{ fontSize: '12px', marginTop: '8px', color: 'var(--color-text-muted)' }}>
            当前威权不足，请先通过诏书和召对提升威权
          </p>
        </div>
      )}
    </div>
  )
}

function BuildingTab({ campaignId }: { campaignId: string }) {
  const [buildings, setBuildings] = useState<{
    buildings: { id: string; name: string; level: number; effect_str: string; constructed: boolean; cost: number }[]
    total_slots: number
  } | null>(null)
  const [constructing, setConstructing] = useState(false)

  useEffect(() => {
    if (!campaignId) return
    api.getBuildings(campaignId).then(res => {
      const data = (res as any).buildings
      setBuildings(data)
    }).catch(() => {
      setBuildings({ buildings: [], total_slots: 5 })
    })
  }, [campaignId])

  const handleConstruct = async (buildingId: string) => {
    setConstructing(true)
    try {
      await api.construct(campaignId, buildingId)
      const res = await api.getBuildings(campaignId)
      setBuildings((res as any).buildings)
    } catch (e) {
      console.error(e)
    }
    setConstructing(false)
  }

  const buildingList = buildings?.buildings || []
  const totalSlots = buildings?.total_slots || 5

  return (
    <div className="fade-in">
      <div className="buildings-header">
        <span className="buildings-slots">建筑槽位: {buildingList.filter(b => b.constructed).length}/{totalSlots}</span>
      </div>

      <div className="buildings-grid">
        {buildingList.map(b => (
          <div key={b.id} className={`building-card ${b.constructed ? 'building-card--built' : ''}`}>
            <div className="building-card__header">
              <span className="building-card__name">{b.name}</span>
              {b.constructed && <span className="building-card__level">Lv.{b.level}</span>}
            </div>
            <div className="building-card__effect">{b.effect_str}</div>
            {!b.constructed && (
              <button
                className="btn btn--primary building-card__build"
                onClick={() => handleConstruct(b.id)}
                disabled={constructing || buildingList.filter(x => x.constructed).length >= totalSlots}
              >
                {b.cost > 0 ? `建造 (${b.cost}万两)` : '建造'}
              </button>
            )}
          </div>
        ))}
      </div>

      {buildingList.length === 0 && (
        <div className="empty-state">
          <p>暂无建筑数据</p>
        </div>
      )}
    </div>
  )
}

function LogTab({ entries }: { entries: { time: string; text: string; important?: boolean }[] }) {
  return (
    <div className="fade-in">
      <div className="card" style={{ padding: '0', maxHeight: '500px', overflow: 'auto' }}>
        {entries.length === 0 && <div className="empty-state">暂无日志</div>}
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

function MapTab() {
  const [selectedRegion, setSelectedRegion] = useState<any>(null)

  const mockRegions = [
    { id: 'luoyang', name: '洛阳', kind: 'capital', unrest: 45, public_support: 60, controlled_by: 'caowei', status: 'controlled' },
    { id: 'chang_an', name: '长安', kind: 'capital', unrest: 70, public_support: 40, controlled_by: 'liubei', status: 'controlled' },
    { id: 'yuzhou', name: '豫州', kind: 'province', unrest: 30, public_support: 70, controlled_by: 'caowei', status: 'controlled' },
    { id: 'yanzhou', name: '兖州', kind: 'province', unrest: 55, public_support: 50, controlled_by: 'caowei', status: 'controlled' },
    { id: 'jingzhou', name: '荆州', kind: 'province', unrest: 40, public_support: 65, controlled_by: 'sunquan', status: 'allied' },
    { id: 'yangzhou', name: '扬州', kind: 'province', unrest: 25, public_support: 75, controlled_by: 'sunquan', status: 'allied' },
    { id: 'xuzhou', name: '徐州', kind: 'province', unrest: 60, public_support: 45, controlled_by: 'caowei', status: 'controlled' },
    { id: 'yizhou', name: '益州', kind: 'province', unrest: 35, public_support: 68, controlled_by: 'liubei', status: 'allied' },
  ]

  return (
    <div className="fade-in">
      <ProvinceMap
        regions={mockRegions}
        onProvinceClick={(region) => setSelectedRegion(region)}
        selectedProvinceId={selectedRegion?.id}
      />
      {selectedRegion && (
        <div className="map-region-detail">
          <h4>{selectedRegion.name}</h4>
          <div className="region-detail-stats">
            <div>动荡程度: {selectedRegion.unrest}%</div>
            <div>民心: {selectedRegion.public_support}%</div>
            <div>控制势力: {selectedRegion.controlled_by}</div>
          </div>
        </div>
      )}
    </div>
  )
}

function OrdersTab({ secretOrders, onRefresh }: { secretOrders: SecretOrder[]; onRefresh: () => void }) {
  useEffect(() => {
    onRefresh()
  }, [onRefresh])

  return (
    <div className="fade-in">
      <div className="card">
        <div style={{ marginBottom: '16px', color: 'var(--color-gold)' }}>密令追踪</div>
        {secretOrders.length === 0 ? (
          <div className="empty-state">暂无密令</div>
        ) : (
          <div>
            {secretOrders.map(order => (
              <div key={order.id} className="secret-order" style={{ marginBottom: '12px' }}>
                <div className="secret-order__header">
                  <span className="secret-order__title">{order.title}</span>
                  <span className="secret-order__status">{order.status}</span>
                </div>
                <div className="secret-order__meta">
                  <span>对象: {order.targetName}</span>
                  <span>{order.issuedAt}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function getAuthorityTier(authority: number): string {
  if (authority >= 90) return '帝'
  if (authority >= 70) return '王'
  if (authority >= 50) return '侯'
  if (authority >= 30) return '伯'
  if (authority >= 15) return '士'
  if (authority >= 5) return '民'
  return '仆'
}