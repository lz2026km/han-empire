// v2.0.0 Phase 3.1: 抽自 App.tsx:691-776 (86 行)
// 汉风术语："天子"通过威权（authority）解锁技能树；
//          经略/权谋/武功/文治 为帝王四维成长树
import { useState, useEffect } from 'react'
import { api } from '../../api'

interface SkillTabProps {
  campaignId: string
}

interface SkillTreeState {
  branches: Record<string, { id: string; name: string; cost: number; tier: number; unlocked: boolean }[]>
  authority_required: number
  skill_points: number
}

export function SkillTab({ campaignId }: SkillTabProps) {
  const [skillTree, setSkillTree] = useState<SkillTreeState | null>(null)
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
                <button type="button"
                  key={skill.id}
                  className={`skill-node ${skill.unlocked ? 'skill-node--unlocked' : 'skill-node--locked'}`}
                  onClick={() => !skill.unlocked && handleActivate(skill.id)}
                  disabled={skill.unlocked || activating === skill.id}
                  title={`消耗 ${skill.cost} 点`}
                >
                  <div className="skill-node-name">{skill.name}</div>
                  <div className="skill-node-tier">阶{skill.tier}</div>
                  {skill.unlocked && <div className="skill-node-check">已开</div>}
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
