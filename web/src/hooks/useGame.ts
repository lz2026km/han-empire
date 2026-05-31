/* =============================================
   useGame - React Hook for game state management
   ============================================= */
import { useState, useCallback } from 'react'
import { api } from '../api'
import type { GameState, MinisterStats, FactionStats, Campaign } from '../types'

export function useGame() {
  const [campaignId, setCampaignId] = useState<string | null>(null)
  const [gameState, setGameState] = useState<GameState | null>(null)
  const [ministers, setMinisters] = useState<MinisterStats[]>([])
  const [factions, setFactions] = useState<FactionStats[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [log, setLog] = useState<{ time: string; text: string; important?: boolean }[]>([])

  const addLog = useCallback((text: string, important = false) => {
    const now = new Date()
    const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
    setLog(prev => [{ time, text, important }, ...prev].slice(0, 200))
  }, [])

  const createCampaign = useCallback(async (emperorName: string, ministerNames: string[]) => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.createCampaign(emperorName, ministerNames)
      setCampaignId(res.campaign_id)
      addLog(`新朝建立：${emperorName}`)
      await loadCampaign(res.campaign_id)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const loadCampaign = useCallback(async (cid: string) => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.getCampaign(cid)
      setCampaignId(cid)
      setGameState(res.state)
      setMinisters(res.ministers)
      setFactions(res.factions)
      addLog(`读档成功：${cid}`)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const issueDecree = useCallback(async (decreeType: string, targetId?: number) => {
    if (!campaignId) return
    setLoading(true)
    try {
      const res = await api.issueDecree(campaignId, decreeType, targetId)
      setGameState(res.game_state)
      addLog(res.result.message, !res.result.success)
      return res.result
    } catch (e: any) {
      setError(e.message)
      return null
    } finally {
      setLoading(false)
    }
  }, [campaignId])

  const nextTurn = useCallback(async () => {
    if (!campaignId) return
    setLoading(true)
    try {
      const res = await api.nextTurn(campaignId)
      await loadCampaign(campaignId)
      addLog(res.result)
      return res.result
    } catch (e: any) {
      setError(e.message)
      return null
    } finally {
      setLoading(false)
    }
  }, [campaignId, loadCampaign])

  const saveGame = useCallback(async () => {
    if (!campaignId) return
    try {
      const res = await api.saveGame(campaignId)
      addLog('存档成功', true)
      return res.message
    } catch (e: any) {
      setError(e.message)
      return null
    }
  }, [campaignId])

  const refresh = useCallback(async () => {
    if (campaignId) await loadCampaign(campaignId)
  }, [campaignId, loadCampaign])

  return {
    campaignId,
    gameState,
    ministers,
    factions,
    loading,
    error,
    log,
    setError,
    createCampaign,
    loadCampaign,
    issueDecree,
    nextTurn,
    saveGame,
    refresh,
    addLog,
  }
}