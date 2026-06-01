// ============================================
// 汉献帝之末路 v2.5.0 — 玉玺砸印动效 ImperialSeal
// 砸下动效 + 朱泥飞溅 + 龙纹闪动
// ============================================

import React, { useEffect, useState } from 'react';
import './ImperialSeal.css';

export interface ImperialSealProps {
  active: boolean;
  onComplete?: () => void;
  authority?: number;       // 1-5 决定颜色
  text?: string;            // 玉玺铭文
}

const AUTHORITY_COLORS: Record<number, { primary: string; ink: string; glow: string }> = {
  1: { primary: '#94a3b8', ink: '#dc2626', glow: 'rgba(148, 163, 184, 0.5)' },
  2: { primary: '#06b6d4', ink: '#dc2626', glow: 'rgba(6, 182, 212, 0.5)' },
  3: { primary: '#3b82f6', ink: '#dc2626', glow: 'rgba(59, 130, 246, 0.6)' },
  4: { primary: '#8b5cf6', ink: '#dc2626', glow: 'rgba(139, 92, 246, 0.6)' },
  5: { primary: '#f59e0b', ink: '#dc2626', glow: 'rgba(245, 158, 11, 0.7)' },
};

export const ImperialSeal: React.FC<ImperialSealProps> = ({
  active,
  onComplete,
  authority = 3,
  text = '受命于天',
}) => {
  const [phase, setPhase] = useState<'idle' | 'raising' | 'striking' | 'settled'>('idle');
  const colors = AUTHORITY_COLORS[authority] || AUTHORITY_COLORS[3];

  useEffect(() => {
    if (!active) {
      setPhase('idle');
      return;
    }
    setPhase('raising');
    const t1 = setTimeout(() => setPhase('striking'), 300);
    const t2 = setTimeout(() => setPhase('settled'), 700);
    const t3 = setTimeout(() => {
      setPhase('idle');
      onComplete?.();
    }, 1500);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [active, onComplete]);

  if (phase === 'idle') return null;

  return (
    <div className={`imperial-seal imperial-seal-${phase}`}>
      {/* 玉玺本体 */}
      <div
        className="imperial-seal-body"
        style={{
          background: `linear-gradient(180deg, ${colors.primary} 0%, #0a0a0d 100%)`,
          boxShadow: `0 0 32px ${colors.glow}`,
        }}
      >
        {/* 顶部龙纹纽 */}
        <div className="imperial-seal-dragon">龍</div>
        {/* 印面 */}
        <div
          className="imperial-seal-face"
          style={{ background: colors.ink, color: '#fef3c7' }}
        >
          <div className="imperial-seal-text">{text}</div>
        </div>
      </div>

      {/* 朱泥飞溅 (砸下时) */}
      {phase === 'striking' && (
        <div className="imperial-seal-splash">
          {Array.from({ length: 8 }).map((_, i) => {
            const angle = (i * 45 * Math.PI) / 180;
            return (
              <div
                key={i}
                className="imperial-seal-splash-drop"
                style={{
                  background: colors.ink,
                  transform: `translate(${Math.cos(angle) * 80}px, ${Math.sin(angle) * 80}px)`,
                }}
              />
            );
          })}
        </div>
      )}

      {/* 印文留痕 (砸下后) */}
      {phase === 'settled' && (
        <div
          className="imperial-seal-mark"
          style={{ color: colors.ink, textShadow: `0 0 16px ${colors.glow}` }}
        >
          {text}
        </div>
      )}
    </div>
  );
};

export default ImperialSeal;
