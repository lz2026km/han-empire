/* =============================================
   App.tsx - Main Application Component
   汉献帝之末路 - React Frontend
   ============================================= */
import { useState, useEffect } from 'react'
import { Header } from './components/Header'
import { useGame } from './hooks/useGame'
import { MinisterChat } from './components/MinisterChat'
import type { GameState, MinisterStats, FactionStats } from './types'
import './styles/app.css'
import { api } from './api'

type Tab = 'overview' | 'decree' | 'ministers' | 'factions' | 'skills' | 'buildings' | 'log' | 'chat'

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [showNewGameModal, setShowNewGameModal] = useState(false)
  const [emperorName, setEmperorName] = useState('刘协')

  const {
    campaignId, gameState, ministers, factions, loading, error, log,
    createCampaign, saveGame, issueDecree, nextTurn
  } = useGame()

  const handleNewGame = async () => {
    setShowNewGameModal(false)
    await createCampaign(emperorName, [])
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: '🏠 总览' },
    { id: 'decree', label: '📜 诏书' },
    { id: 'chat', label: '💬 召对' },
    { id: 'ministers', label: '👥 大臣' },
    { id: 'factions', label: '⚔️ 派系' },
    { id: 'skills', label: '🌲 技能' },
    { id: 'buildings', label: '🏛️ 建筑' },
    { id: 'log', label: '📋 日志' },
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

              {activeTab === 'overview' && (
                <OverviewTab gameState={gameState} ministers={ministers} factions={factions} onNextTurn={nextTurn} />
              )}
              {activeTab === 'decree' && (
                <DecreeTab gameState={gameState} ministers={ministers} onIssue={issueDecree} />
              )}
              {activeTab === 'chat' && campaignId && (
                <MinisterChat campaignId={campaignId} ministers={ministers} />
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
              {activeTab === 'log' && (
                <LogTab entries={log} />
              )}
            </>
          )}
        </div>
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
  gameState, ministers, factions, onNextTurn
}: {
  gameState: GameState | null
  ministers: MinisterStats[]
  factions: FactionStats[]
  onNextTurn: () => void
}) {
  if (!gameState) return null
  return (
    <div className="fade-in">
      <div className="action-row">
        <button className="btn btn--primary" onClick={onNextTurn}>⏭️ 下一个月</button>
        <button className="btn btn--gold">💾 存档</button>
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
  return (
    <div className="fade-in">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '12px' }}>
        {ministers.map(m => (
          <div key={m.id} className="minister-card">
            <div className="minister-card__portrait">
              {m.name.charAt(0)}
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
    </div>
  )
}

function FactionTab({ factions }: { factions: FactionStats[] }) {
  return (
    <div className="fade-in">
      <div className="faction-panel">
        {factions.map(f => (
          <div key={f.id} className="faction-card">
            <div className="faction-card__header">
              <span className="faction-card__name">{f.name}</span>
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

function getAuthorityTier(authority: number): string {
  if (authority >= 90) return '帝'
  if (authority >= 70) return '王'
  if (authority >= 50) return '侯'
  if (authority >= 30) return '伯'
  if (authority >= 15) return '士'
  if (authority >= 5) return '民'
  return '仆'
}