// ============================================
// 汉献帝之末路 v2.5.0 — 5 档旨意权限滑块 AuthoritySlider
// 口谕 / 谕旨 / 圣旨 / 密旨 / 廷议
// ============================================

import React from 'react';
import './AuthoritySlider.css';

export type AuthorityLevel = 1 | 2 | 3 | 4 | 5;

export interface AuthoritySliderProps {
  value: AuthorityLevel;
  onChange: (v: AuthorityLevel) => void;
  disabled?: boolean;
}

const AUTHORITY_LEVELS: Array<{
  level: AuthorityLevel;
  name: string;
  color: string;
  desc: string;
  icon: string;
}> = [
  { level: 1, name: '口谕', color: '#94a3b8', desc: '当面口述, 轻诺', icon: '召对' },
  { level: 2, name: '谕旨', color: '#06b6d4', desc: '颁行州郡, 中度', icon: '诏书' },
  { level: 3, name: '圣旨', color: '#3b82f6', desc: '昭告天下, 高度', icon: '页' },
  { level: 4, name: '密旨', color: '#8b5cf6', desc: '暗授亲信, 高度隐秘', icon: '安全' },
  { level: 5, name: '廷议', color: '#f59e0b', desc: '朝会议定, 最高权威', icon: '权' },
];

export const AuthoritySlider: React.FC<AuthoritySliderProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  return (
    <div className={`authority-slider ${disabled ? 'authority-slider-disabled' : ''}`}>
      <input
        type="range"
        min={1}
        max={5}
        step={1}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value) as AuthorityLevel)}
        className="authority-slider-input"
        aria-label="旨意权限"
        style={{
          background: `linear-gradient(90deg, ${AUTHORITY_LEVELS[0].color} 0%, ${AUTHORITY_LEVELS[value - 1].color} 100%)`,
        }}
      />
      <div className="authority-slider-marks">
        {AUTHORITY_LEVELS.map((a) => (
          <button type="button"
            key={a.level}
            className={`authority-slider-mark ${value === a.level ? 'authority-slider-mark-active' : ''}`}
            style={{ color: a.color }}
            onClick={() => !disabled && onChange(a.level)}
            disabled={disabled}
            title={`${a.name} - ${a.desc}`}
            aria-label={`${a.name}`}
          >
            <span className="authority-slider-mark-icon">{a.icon}</span>
            <span className="authority-slider-mark-name">{a.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default AuthoritySlider;
