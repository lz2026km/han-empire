// ============================================
// 汉献帝之末路 v2.5.0 — 回奏弹窗 VerdictPopup
// 三段折叠: 结果 / 代价 / 隐患
// 打字机效果 + 折叠展开
// ============================================

import React, { useState } from 'react';
import './VerdictPopup.css';

export interface Verdict {
  result: string;       // 实际结果
  cost: string;         // 代价
  hidden: string;       // 隐患
  isSuccess: boolean;
}

export interface VerdictPopupProps {
  verdict: Verdict | null;
  onClose?: () => void;
}

export const VerdictPopup: React.FC<VerdictPopupProps> = ({
  verdict,
  onClose,
}) => {
  const [expanded, setExpanded] = useState<string | null>('result');

  if (!verdict) return null;

  const sections = [
    { key: 'result', label: '结果', content: verdict.result, color: '#3b82f6' },
    { key: 'cost', label: '代价', content: verdict.cost, color: '#f97316' },
    { key: 'hidden', label: '隐患', content: verdict.hidden, color: '#ef4444' },
  ];

  return (
    <div className="verdict-popup" role="dialog" aria-label="回奏">
      <div className="verdict-popup-header">
        <h3 className="verdict-popup-title imperial">
            {verdict.isSuccess ? '旨意达成' : '旨意有变'}
          </h3>
        <button type="button" className="verdict-popup-close" onClick={onClose} aria-label="关闭">×</button>
      </div>
      <div className="verdict-popup-body">
        {sections.map((s) => (
          <div
            key={s.key}
            className={`verdict-section ${expanded === s.key ? 'verdict-section-open' : ''}`}
            style={{ borderColor: s.color }}
          >
            <button type="button"
              className="verdict-section-header"
              onClick={() => setExpanded((cur) => (cur === s.key ? null : s.key))}
              style={{ color: s.color }}
            >
              <span>{s.label}</span>
              <span className="verdict-section-arrow">
                {expanded === s.key ? '▾' : '▸'}
              </span>
            </button>
            {expanded === s.key && (
              <div className="verdict-section-content">
                {s.content}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default VerdictPopup;
