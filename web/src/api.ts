// 静态 GitHub Pages 演示模式 mock 数据
// 当 VITE_DEMO_MODE=true 时使用 (vite.config.ts 自动注入)

import type {
  Campaign, CampaignStateResponse, DecreeResponse,
  EventResponse, SkillTreeResponse, BuildingsResponse,
  FactionInfoResponse, GameSave, DecreeResult, Consort
} from './types'

const IS_DEMO = import.meta.env.VITE_DEMO_MODE === 'true'

// ===== 演示数据 =====
const DEMO_CAMPAIGN: Campaign = {
  id: 'demo-001',
  emperor: '刘协',
  year: 196,
  month: 3,
  day: 15,
  gold: 50000,
  troops: 10000,
  morale: 75,
  prestige: 60,
}

const DEMO_STATE: CampaignStateResponse = {
  campaign: DEMO_CAMPAIGN,
  ministers: [
    { id: 'm1', name: '曹操', faction: '曹党', portrait_id: 'cao_cao', stats: { loyalty: 30, ambition: 95, ability: 95 }, role: '司空', alive: true },
    { id: 'm2', name: '刘备', faction: '皇党', portrait_id: 'liu_bei', stats: { loyalty: 85, ambition: 70, ability: 85 }, role: '左将军', alive: true },
    { id: 'm3', name: '王允', faction: '士族', portrait_id: 'wang_yun', stats: { loyalty: 90, ambition: 60, ability: 80 }, role: '司徒', alive: true },
  ],
  factions: [
    { id: 'f1', name: '士族', influence: 80, friendliness: 50, members: 12 },
    { id: 'f2', name: '宦官', influence: 20, friendliness: 30, members: 5 },
    { id: 'f3', name: '外戚', influence: 60, friendliness: 70, members: 4 },
    { id: 'f4', name: '清流', influence: 70, friendliness: 80, members: 8 },
  ],
}

const DEMO_EVENTS: EventResponse[] = [
  {
    id: 'e1', category: '朝政', title: '朝议许都屯田', description: '曹操奏请推行屯田制于许都',
    urgency: 6, severity: 7, credibility: 8, involves: ['士族', '豪商'], month: 3,
  },
  {
    id: 'e2', category: '军事', title: '袁术称帝', description: '袁术于寿春僭号称帝',
    urgency: 9, severity: 9, credibility: 10, involves: ['袁术', '孙策'], month: 3,
  },
  {
    id: 'e3', category: '财政', title: '许都粮仓告急', description: '今春旱灾, 许都粮仓仅余三月',
    urgency: 8, severity: 7, credibility: 7, involves: ['士族', '豪商'], month: 3,
  },
  {
    id: 'e4', category: '地方', title: '冀州黄巾复起', description: '冀州黄巾余党复聚',
    urgency: 7, severity: 6, credibility: 6, involves: ['黄巾'], month: 3,
  },
  {
    id: 'e5', category: '人物', title: '荀彧求见', description: '尚书令荀彧求见天子, 密陈大事',
    urgency: 5, severity: 5, credibility: 9, involves: ['士族'], month: 3,
  },
]

const DEMO_DECREES: DecreeResponse[] = [
  {
    id: 'd1', campaign_id: 'demo-001', type: 'decree', title: '诏曹操讨袁术',
    content: '朕以大汉天子之名, 诏司空曹操兴兵讨逆, 殄灭袁术僭号之罪...',
    status: 'pending', target: '讨袁术', executor: '曹操', scope: '豫州',
    resources: '银 20 万两 + 兵 5000', deadline: '3 月', authority_level: '圣旨',
    incentive: '封侯 + 赐金', constraints: '不得扰民', publicity: '明发天下',
    created_at: '196-03-15',
  },
  {
    id: 'd2', campaign_id: 'demo-001', type: 'edict', title: '密诏刘备勤王',
    content: '衣带诏: 朕受制于曹贼, 卿可暗中联络忠义, 共图兴复...',
    status: 'pending', target: '勤王', executor: '刘备', scope: '徐州',
    resources: '衣带密诏', deadline: '6 月', authority_level: '密旨',
    incentive: '封王', constraints: '绝对保密', publicity: '面授',
    created_at: '196-03-12',
  },
]

// ===== Mock request 实现 =====
async function mockRequest<T>(path: string, _options?: RequestInit): Promise<T> {
  await new Promise(r => setTimeout(r, 200 + Math.random() * 300))
  if (path === '/health') return { status: 'ok', game: 'han-empire-demo' } as T
  if (path === '/campaigns' || path.startsWith('/campaigns?')) {
    return { campaigns: [DEMO_CAMPAIGN] } as T
  }
  if (path.match(/\/campaigns\/[^/]+$/) || path.match(/\/campaigns\/[^/]+\?/)) {
    return DEMO_STATE as T
  }
  if (path.includes('/events') || path.includes('/memorials')) {
    return { events: DEMO_EVENTS, memorials: DEMO_EVENTS.map(e => ({ ...e, type: 'memorial' })) } as T
  }
  if (path.includes('/directives')) {
    return { directives: DEMO_DECREES } as T
  }
  if (path.includes('/factions')) {
    return { factions: DEMO_STATE.factions } as T
  }
  if (path.includes('/skills')) {
    return { skills: [], unlocked: [], points: 5 } as T
  }
  if (path.includes('/buildings')) {
    return { buildings: [] } as T
  }
  return {} as T
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  if (IS_DEMO) return mockRequest<T>(path, options)
  // 真模式: 用绝对 API_BASE
  const API_BASE = 'http://localhost:5555/api'
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
  return res.json() as Promise<T>
}

// ===== 兼容原 API =====
export const api = {
  health: () => request<{ status: string; game: string }>('/health'),
  listCampaigns: () => request<{ campaigns: Campaign[] }>('/campaigns'),
  createCampaign: (emperorName = '刘协', ministerNames: string[] = []) =>
    request<Campaign>('/campaigns', { method: 'POST', body: JSON.stringify({ emperor_name: emperorName, minister_names: ministerNames }) }),
  getCampaignState: (id: string) => request<CampaignStateResponse>(`/campaigns/${id}`),
  getEvents: (id: string) => request<EventResponse[]>(`/campaigns/${id}/events`),
  getFactions: (id: string) => request<FactionInfoResponse[]>(`/campaigns/${id}/factions`),
  getSkills: (id: string) => request<SkillTreeResponse>(`/campaigns/${id}/skills`),
  getBuildings: (id: string) => request<BuildingsResponse>(`/campaigns/${id}/buildings`),
  listDecrees: (id: string) => request<DecreeResponse[]>(`/campaigns/${id}/decrees`),
  createDecree: (id: string, payload: Partial<DecreeResponse>) =>
    request<DecreeResponse>(`/campaigns/${id}/decrees`, { method: 'POST', body: JSON.stringify(payload) }),
  confirmDecree: (id: string, decreeId: string) =>
    request<DecreeResult>(`/campaigns/${id}/decrees/${decreeId}/confirm`, { method: 'POST' }),
  rejectDecree: (id: string, decreeId: string) =>
    request<DecreeResult>(`/campaigns/${id}/decrees/${decreeId}/reject`, { method: 'POST' }),
  saveGame: (save: GameSave) =>
    request<{ ok: boolean }>('/save', { method: 'POST', body: JSON.stringify(save) }),
  listConsorts: (id: string) => request<{ consorts: Consort[] }>(`/campaigns/${id}/consorts`),
}

export { IS_DEMO }
