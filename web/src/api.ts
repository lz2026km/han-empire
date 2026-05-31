/* =============================================
   REST API Client for han-empire backend
   ============================================= */

import type {
  Campaign, CampaignStateResponse, DecreeResponse,
  EventResponse, SkillTreeResponse, BuildingsResponse,
  FactionInfoResponse, GameSave, DecreeResult
} from './types'

const API_BASE = 'http://localhost:5555/api'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
  return res.json() as Promise<T>
}

// ---- Campaign Management ----

export const api = {
  health: () => request<{ status: string; game: string }>('/health'),

  listCampaigns: () =>
    request<{ campaigns: Campaign[] }>('/campaigns'),

  createCampaign: (emperorName = '刘协', ministerNames: string[] = []) =>
    request<{ campaign_id: string; message: string }>('/campaigns', {
      method: 'POST',
      body: JSON.stringify({ emperor_name: emperorName, minister_names: ministerNames }),
    }),

  getCampaign: (campaignId: string) =>
    request<CampaignStateResponse>(`/campaigns/${campaignId}`),

  // ---- Game Actions ----

  issueDecree: (campaignId: string, decreeType: string, targetId?: number) =>
    request<DecreeResponse>(`/campaigns/${campaignId}/issue_decree`, {
      method: 'POST',
      body: JSON.stringify({ decree_type: decreeType, target_id: targetId }),
    }),

  receiveMinister: (campaignId: string) =>
    request<{ result: string }>(`/campaigns/${campaignId}/receive_minister`, {
      method: 'POST',
    }),

  nextTurn: (campaignId: string) =>
    request<{ result: string }>(`/campaigns/${campaignId}/next_turn`, {
      method: 'POST',
    }),

  checkEvents: (campaignId: string) =>
    request<EventResponse>(`/campaigns/${campaignId}/check_events`),

  triggerEvent: (campaignId: string, eventId: string, choice = 0) =>
    request<{ result: DecreeResult }>(`/campaigns/${campaignId}/trigger_event`, {
      method: 'POST',
      body: JSON.stringify({ event_id: eventId, choice }),
    }),

  // ---- Skill Tree ----

  getSkillTree: (campaignId: string) =>
    request<SkillTreeResponse>(`/campaigns/${campaignId}/skill_tree`),

  unlockSkill: (campaignId: string, skillId: string) =>
    request<{ result: DecreeResult }>(`/campaigns/${campaignId}/unlock_skill`, {
      method: 'POST',
      body: JSON.stringify({ skill_id: skillId }),
    }),

  // ---- Buildings ----

  getBuildings: (campaignId: string) =>
    request<BuildingsResponse>(`/campaigns/${campaignId}/buildings`),

  construct: (campaignId: string, buildingId: string) =>
    request<{ result: DecreeResult }>(`/campaigns/${campaignId}/construct`, {
      method: 'POST',
      body: JSON.stringify({ building_id: buildingId }),
    }),

  // ---- Factions ----

  getFactionInfo: (campaignId: string) =>
    request<FactionInfoResponse>(`/campaigns/${campaignId}/faction_info`),

  adjustFactionInfluence: (campaignId: string, factionId: string, delta: number) =>
    request<{ result: DecreeResult }>(`/campaigns/${campaignId}/faction_influence`, {
      method: 'POST',
      body: JSON.stringify({ faction_id: factionId, delta }),
    }),

  // ---- Save/Load ----

  saveGame: (campaignId: string) =>
    request<{ message: string }>(`/campaigns/${campaignId}/save`, {
      method: 'POST',
    }),

  loadGame: (campaignId: string) =>
    request<{ message: string }>(`/campaigns/${campaignId}/load`, {
      method: 'POST',
    }),

  listSaves: (campaignId: string) =>
    request<{ saves: GameSave[] }>(`/campaigns/${campaignId}/saves`),

  deleteSave: (campaignId: string, slot: number) =>
    request<{ message: string }>(`/campaigns/${campaignId}/saves/${slot}`, {
      method: 'DELETE',
    }),

  // ---- SSE Streaming ----

  streamSettlement: (campaignId: string) =>
    new EventSource(`${API_BASE}/campaigns/${campaignId}/stream_settlement`),

  // ---- Chat ----

  chatWithMinister: (campaignId: string, ministerName: string, message: string) =>
    request<{ result: string; chat_history?: { role: string; text: string }[] }>(
      `/campaigns/${campaignId}/chat/${encodeURIComponent(ministerName)}`,
      {
        method: 'POST',
        body: JSON.stringify({ message }),
      }
    ),

  // ---- Secret Orders ----

  getSecretOrders: (campaignId: string) =>
    request<{ orders: SecretOrder[] }>(`/campaigns/${campaignId}/secret_orders`),

  createSecretOrder: (campaignId: string, order: { title: string; content: string; assignee: string; deadline_months?: number }) =>
    request<{ order: SecretOrder }>(`/campaigns/${campaignId}/secret_orders`, {
      method: 'POST',
      body: JSON.stringify(order),
    }),

  cancelSecretOrder: (campaignId: string, orderId: string) =>
    request<{ message: string }>(`/campaigns/${campaignId}/secret_orders/${orderId}`, {
      method: 'DELETE',
    }),

  // ---- Cheat Commands ----

  executeCheat: (campaignId: string, command: string, args?: Record<string, any>) =>
    request<{ success: boolean; output: string }>(`/campaigns/${campaignId}/cheat`, {
      method: 'POST',
      body: JSON.stringify({ command, args }),
    }),
}

export interface SecretOrder {
  id: string
  title: string
  content: string
  targetName: string
  issuedAt: string
  status: 'pending' | 'executing' | 'completed' | 'failed' | 'exposed'
  result?: string
}