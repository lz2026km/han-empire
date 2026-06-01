// ============================================
// 汉献帝之末路 v2.5.0 — 大臣发言气泡 DebateBubble
// 淡入 + 立场色码 + 文字打字
// ============================================

import React, { useEffect, useState } from 'react';

export type Stance = 'support' | 'oppose' | 'neutral';

export interface DebateBubbleProps {
  speaker: string;
  line: string;
  stance?: Stance;
  typewriter?: boolean;
  duration?: number;
  onClose?: () => void;
}

const STANCE_COLORS: Record<Stance, { fg: string; bg: string; border: string; tag: string }> = {
  support: { fg: '#3b82f6', bg: 'rgba(59, 130, 246, 0.12)', border: '#3b82f6', tag: '赞成' },
  oppose: { fg: '#ef4444', bg: 'rgba(239, 68, 68, 0.12)', border: '#ef4444', tag: '反对' },
  neutral: { fg: '#f59e0b', bg: 'rgba(245, 158, 11, 0.12)', border: '#f59e0b', tag: '中立' },
};

export const DebateBubble: React.FC<DebateBubbleProps> = ({
  speaker,
  line,
  stance = 'neutral',
  typewriter = true,
  duration = 3000,
  onClose,
}) => {
  const [displayText, setDisplayText] = useState(typewriter ? '' : line);
  const color = STANCE_COLORS[stance];

  // 打字机效果
  useEffect(() => {
    if (!typewriter) return;
    let i = 0;
    const id = setInterval(() => {
      i++;
      setDisplayText(line.slice(0, i));
      if (i >= line.length) clearInterval(id);
    }, 50);
    return () => clearInterval(id);
  }, [line, typewriter]);

  // 自动关闭
  useEffect(() => {
    if (!duration) return;
    const id = setTimeout(() => onClose?.(), duration);
    return () => clearTimeout(id);
  }, [duration, onClose]);

  return (
    <div
      className="debate-bubble"
      style={{
        color: color.fg,
        background: color.bg,
        borderColor: color.border,
      }}
      role="status"
      aria-live="polite"
    >
      <div className="debate-bubble-header">
        <span className="debate-bubble-speaker">{speaker}</span>
        <span
          className="debate-bubble-stance"
          style={{ background: color.border }}
        >
          {color.tag}
        </span>
      </div>
      <div className="debate-bubble-line">
        {displayText}
        {typewriter && displayText.length < line.length && (
          <span className="debate-bubble-cursor">▌</span>
        )}
      </div>
    </div>
  );
};

export default DebateBubble;
