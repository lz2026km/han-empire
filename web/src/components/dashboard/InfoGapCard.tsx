// ============================================
// 汉献帝之末路 v2.5.0 — 信息差揭示卡 InfoGapCard
// 揭示/未揭示 翻转 + 模糊度动效
// ============================================

import React, { useState } from 'react';
import './InfoGapCard.css';

export interface InfoGapCardProps {
  revealed: boolean;
  title: string;
  hint: string;       // 未揭示时的提示
  content: string;    // 揭示后的内容
  source?: string;    // 情报来源
  onReveal?: () => void;
}

export const InfoGapCard: React.FC<InfoGapCardProps> = ({
  revealed,
  title,
  hint,
  content,
  source,
  onReveal,
}) => {
  const [showContent, setShowContent] = useState(revealed);

  const handleReveal = () => {
    if (!showContent) {
      setShowContent(true);
      onReveal?.();
    }
  };

  return (
    <div
      className={`info-gap ${showContent ? 'info-gap-revealed' : 'info-gap-hidden'}`}
      onClick={handleReveal}
      role="button"
      tabIndex={0}
    >
      <div className="info-gap-header">
        <span className="info-gap-title">{title}</span>
        <span className="info-gap-status">
          {showContent ? '已揭示' : '未揭示'}
        </span>
      </div>
      <div className="info-gap-body">
        {showContent ? (
          <>
            <div className="info-gap-content">{content}</div>
            {source && <div className="info-gap-source">— {source}</div>}
          </>
        ) : (
          <div className="info-gap-hint">
            <span className="info-gap-blur">{hint}</span>
            <div className="info-gap-cta">点此揭示 ▾</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InfoGapCard;
