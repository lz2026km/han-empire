/* =============================================
   TopHUD - 顶部状态栏 (v5.4.0 P7-A4)
   顶部 parchment 横条, 显示核心 4 指标
   年月 / 国库 / 内库 / 民心 / 皇威
   ============================================= */
import { useEffect, useState } from 'react'
import { api } from '../api'

interface Metrics {
  turn?: number
  year?: number
  month?: number
  metrics?: Record<string, number>
  budget?: {
    汉室库?: { balance: number; net: number }
    内库?: { balance: number; net: number }
  } | null
}

interface TopHUDProps {
  campaignId: string | null
  fallback?: {
    metrics?: Record<string, number>
    year?: number
    month?: number
    turn?: number
  } | null
}

function formatMoney(n: number) {
  return `${n}万两`
}

function getAuthorityTier(authority: number): string {
  if (authority >= 90) return '九五之尊'
  if (authority >= 75) return '乾纲独断'
  if (authority >= 60) return '亲贤辅政'
  if (authority >= 45) return '垂拱而治'
  if (authority >= 30) return '受制于人'
  if (authority >= 15) return '寄人篱下'
  return '待宰羔羊'
}

function getTrustTier(trust: number): string {
  if (trust >= 80) return '民心思汉'
  if (trust >= 60) return '民心向化'
  if (trust >= 40) return '民心安定'
  if (trust >= 20) return '民心离散'
  return '天下苦秦'
}

export function TopHUD({ campaignId, fallback }: TopHUDProps) {
  const [data, setData] = useState<Metrics | null>(null)

  useEffect(() => {
    if (!campaignId) {
      setData(null)
      return
    }
    let cancelled = false
    const fetchData = async () => {
      try {
        const r = await api.getCampaignStats(campaignId)
        if (!cancelled) setData(r)
      } catch (e) {
      }
    }
    fetchData()
    const onVisibility = () => {
      if (document.visibilityState === 'visible') fetchData()
    }
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      cancelled = true
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [campaignId])

  if (!campaignId) return null

  const m = (fallback?.metrics || data?.metrics || {}) as Record<string, number>
  const year = fallback?.year ?? data?.year ?? 189
  const month = fallback?.month ?? 1
  const turn = fallback?.turn ?? 0

  const guoku = (data?.budget?.汉室库?.balance ?? m['汉室库'] ?? 0) as number
  const neiku = (data?.budget?.内库?.balance ?? m['内库'] ?? 0) as number
  const guokuNet = (data?.budget?.汉室库?.net ?? 0) as number
  const neikuNet = (data?.budget?.内库?.net ?? 0) as number

  const authority = m['威权'] ?? 15
  const trust = m['声望'] ?? 30
  const faction = m['藩镇'] ?? 80

  return (
    <div className="top-hud" role="status" aria-label="顶部状态栏">
      <div className="top-hud__group top-hud__group--year">
        <span className="top-hud__year-num">{year}</span>
        <span className="top-hud__year-month">年{month}月</span>
        <span className="top-hud__turn">第{turn}回合</span>
      </div>

      <div className="top-hud__group">
        <span className="top-hud__label">国库</span>
        <span className="top-hud__num">{formatMoney(guoku)}</span>
        <span className={`top-hud__delta ${guokuNet >= 0 ? 'top-hud__delta--pos' : 'top-hud__delta--neg'}`}>
          月{guokuNet >= 0 ? '+' : ''}{guokuNet}万两
        </span>
      </div>

      <div className="top-hud__group">
        <span className="top-hud__label">内库</span>
        <span className="top-hud__num">{formatMoney(neiku)}</span>
        <span className={`top-hud__delta ${neikuNet >= 0 ? 'top-hud__delta--pos' : 'top-hud__delta--neg'}`}>
          月{neikuNet >= 0 ? '+' : ''}{neikuNet}万两
        </span>
      </div>

      <div className="top-hud__group top-hud__group--trust">
        <span className="top-hud__label">民心</span>
        <span className="top-hud__num">{trust}</span>
        <span className="top-hud__tier">{getTrustTier(trust)}</span>
      </div>

      <div className="top-hud__group top-hud__group--authority">
        <span className="top-hud__label">皇威</span>
        <span className="top-hud__num">{authority}</span>
        <span className="top-hud__tier">{getAuthorityTier(authority)}</span>
      </div>

      <div className="top-hud__group top-hud__group--faction" title="藩镇割据程度">
        <span className="top-hud__label">藩镇</span>
        <span className="top-hud__num">{faction}</span>
      </div>
    </div>
  )
}
