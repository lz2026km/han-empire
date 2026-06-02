// ============================================
// 汉献帝之末路 v2.5.0 — 党派反弹徽章 FactionBacklashBadge
// 4 状态 (无/拖延/曲解/反扑) + 动效提醒
// ============================================

import React from 'react';
import './FactionBacklashBadge.css';

export type BacklashState = 'none' | 'delay' | 'twist' | 'revolt';

export interface FactionBacklashBadgeProps {
  state: BacklashState;
  faction?: string;
  detail?: string;
  count?: number;
}

const BACKLASH_CONFIG: Record<BacklashState, { label: string; color: string; icon: string; desc: string }> = {
  none: { label: '无反弹', color: '#64748b', icon: '✓', desc: '执行顺利' },
  delay: { label: '拖延', color: '#f97316', icon: '⏳', desc: '执行迟缓' },
  twist: { label: '曲解', color: '#8b5cf6', icon: '∿', desc: '曲解旨意' },
  revolt: { label: '反扑', color: '#ef4444', icon: '⚠', desc: '公开抗旨' },
};

export const FactionBacklashBadge: React.FC<FactionBacklashBadgeProps> = ({
  state,
  faction,
  detail,
  count = 1,
}) => {
  const cfg = BACKLASH_CONFIG[state];
  return (
    <div
      className={`backlash-badge backlash-badge-${state} ${state !== 'none' ? 'backlash-badge-active' : ''}`}
      style={{ color: cfg.color, borderColor: cfg.color }}
      title={detail || cfg.desc}
      role="status"
    >
      <span className="backlash-badge-icon">{cfg.icon}</span>
      <span className="backlash-badge-text">
        {faction && <span className="backlash-badge-faction">{faction}</span>}
        {cfg.label}
      </span>
      {count > 1 && <span className="backlash-badge-count">×{count}</span>}
    </div>
  );
};

export default FactionBacklashBadge;
