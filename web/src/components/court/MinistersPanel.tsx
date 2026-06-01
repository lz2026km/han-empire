// ============================================
// 汉献帝之末路 v2.5.0 — 大臣立绘面板 MinistersPanel
// 3-5 张立绘 + hover 立场 + 选中发光
// ============================================

import React from 'react';
import type { MinisterStats } from '../../types';

export interface MinistersPanelProps {
  ministers: MinisterStats[];
  activeSpeaker?: string | null;
  onMinisterClick?: (m: MinisterStats) => void;
}

const FACTION_COLORS: Record<string, string> = {
  '主公': '#3b82f6',
  '汉室': '#3b82f6',
  '阉党': '#ef4444',
  '士族': '#f59e0b',
  '外戚': '#8b5cf6',
};

export const MinistersPanel: React.FC<MinistersPanelProps> = ({
  ministers,
  activeSpeaker,
  onMinisterClick,
}) => {
  // 1 主公 + 最多 5 大臣 = 6 位
  const displayMinisters = ministers.slice(0, 5);

  return (
    <div className="ministers-panel">
      {displayMinisters.map((m, i) => {
        const color = FACTION_COLORS[m.faction] || '#94a3b8';
        const isActive = activeSpeaker === m.id;
        return (
          <div
            key={m.id || i}
            className={`minister ${isActive ? 'minister-active' : ''}`}
            style={{ '--faction-color': color } as React.CSSProperties}
            onClick={() => onMinisterClick?.(m)}
            role="button"
            tabIndex={0}
            aria-label={`${m.name} ${m.title}`}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') onMinisterClick?.(m);
            }}
          >
            <div className="minister-silhouette">
              <div className="minister-hat">冠</div>
              <div className="minister-body">
                {m.portrait || m.name?.[0] || '?'}
              </div>
            </div>
            <div className="minister-name">{m.name}</div>
            <div className="minister-title">{m.title}</div>
            <div className="minister-faction-tag" style={{ color }}>
              {m.faction}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default MinistersPanel;
