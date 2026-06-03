// ============================================
// 汉献帝之末路 v3.0 — 好感度环形图 IntimacyRing
// 极简 SVG 圆环, 蓝调蓝紫渐变
// ============================================

import React from 'react';

export interface IntimacyRingProps {
  value: number;        // 0-100
  max?: number;         // 默认 100
  label?: string;       // "好感度" / "忠诚度"
  size?: number;        // 直径 (默认 80)
  color?: 'blue' | 'green' | 'amber' | 'red';
  showValue?: boolean;
}

const COLORS = {
  blue:   { start: '#3b82f6', end: '#60a5fa' },
  green:  { start: '#10b981', end: '#34d399' },
  amber:  { start: '#f59e0b', end: '#fbbf24' },
  red:    { start: '#ef4444', end: '#f87171' },
};

export function IntimacyRing({
  value,
  max = 100,
  label = '好感度',
  size = 80,
  color = 'blue',
  showValue = true,
}: IntimacyRingProps) {
  const pct = Math.max(0, Math.min(value / max, 1));
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - pct);
  const palette = COLORS[color];

  return (
    <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <defs>
          <linearGradient id={`grad-${color}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={palette.start} />
            <stop offset="100%" stopColor={palette.end} />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth={4}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={`url(#grad-${color})`}
          strokeWidth={4}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: 'stroke-dashoffset 0.4s ease' }}
        />
        {showValue && (
          <text
            x="50%"
            y="50%"
            textAnchor="middle"
            dominantBaseline="central"
            fill="#e8e8ea"
            fontSize={size / 4}
            fontWeight={600}
          >
            {Math.round(pct * 100)}
          </text>
        )}
      </svg>
      {label && <div style={{ fontSize: 11, color: '#9ca3af' }}>{label}</div>}
    </div>
  );
}

export default IntimacyRing;
