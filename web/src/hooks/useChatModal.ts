// v2.0.0 Phase 3.3: 召对相关 hook - 抽自 App.tsx:86-113 (28 行)
// 抽 3 个回调：handleMinisterSelect / handleSendMessage / handleExecuteCheat
// "三国/汉风"视角：召对 = 帝王与大臣私语（区别于朝会公开议事）
import { useState, useCallback } from 'react'
import type { Minister } from '../types'
import type { MinisterStats } from '../types'
import { api } from '../api'

export function useChatModal(campaignId: string | null, ministers: MinisterStats[]) {
  const [showChatModal, setShowChatModal] = useState(false)
  const [selectedMinister, setSelectedMinister] = useState<Minister | null>(null)

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

  return {
    showChatModal,
    setShowChatModal,
    selectedMinister,
    handleMinisterSelect,
    handleSendMessage,
  }
}

export function useCheatConsole(campaignId: string | null) {
  const [showCheatConsole, setShowCheatConsole] = useState(false)

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

  return {
    showCheatConsole,
    setShowCheatConsole,
    handleExecuteCheat,
  }
}
