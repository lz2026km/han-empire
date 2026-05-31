/* =============================================
   汉献帝之末路 - TypeScript类型定义
   ============================================= */

export interface GameState {
  campaign_id: string
  year: number
  month: number
  emperor_name: string
  emperor_authority: number
  emperor_loyalty: number
  faction_influence: Record<string, number>
  available_decree_types: string[]
  turn_count: number
  game_over: boolean
  victory: boolean
}

export interface Minister {
  id: number
  name: string
  faction: string
  loyalty: number
  ability: number
  position: string
  portrait?: string
}

export interface MinisterStats extends Minister {
  id: number
  name: string
  faction: string
  loyalty: number
  ability: number
  position: string
  authority_cost?: number
  skill_bonuses?: Record<string, number>
}

export interface Faction {
  id: string
  name: string
  leader_name: string
  influence: number
  color: string
  description: string
}

export interface FactionStats extends Faction {
  influence: number
  dominant_ministers: number
}

export interface DecreeCard {
  decree_type: string
  name: string
  effect_str: string
  cost: number
  tier: number
}

export interface DecreeResult {
  success: boolean
  message: string
  authority_delta: number
  faction_delta: Record<string, number>
  minister_changes: Record<string, number>
  random_event?: string
}

export interface EventChoice {
  index: number
  text: string
  outcomes: Record<string, number | string>
}

export interface GameEvent {
  id: string
  name: string
  description: string
  choices: EventChoice[]
}

export interface SkillNode {
  id: string
  name: string
  branch: string
  tier: number
  effect_str: string
  cost: number
  unlocked: boolean
  prereqs: string[]
}

export interface SkillTree {
  branches: Record<string, SkillNode[]>
  authority_required: number
  unlocked_skills: string[]
}

export interface Building {
  id: string
  name: string
  level: number
  max_level: number
  effect_str: string
  cost: number
  constructed: boolean
}

export interface BuildingsData {
  buildings: Building[]
  total_slots: number
  used_slots: number
}

export interface Campaign {
  id: string
  year: number
  emperor_authority: number
  created: number
}

export interface GameSave {
  slot: number
  campaign_id: string
  timestamp: number
  year: number
  authority: number
}

// API Response types
export interface ApiResponse<T> {
  data?: T
  error?: string
}

export interface CampaignListResponse {
  campaigns: Campaign[]
}

export interface CampaignStateResponse {
  campaign_id: string
  state: GameState
  ministers: MinisterStats[]
  factions: FactionStats[]
}

export interface DecreeResponse {
  result: DecreeResult
  game_state: GameState
}

export interface EventResponse {
  events: GameEvent[]
}

export interface SkillTreeResponse {
  skill_tree: SkillTree
}

export interface BuildingsResponse {
  buildings: BuildingsData
}

export interface FactionInfoResponse {
  factions: FactionStats[]
}

// Component prop types
export interface TabItem {
  id: string
  label: string
  icon?: string
}

export interface ActionButton {
  label: string
  onClick: () => void
  variant?: 'primary' | 'gold' | 'default'
  disabled?: boolean
}