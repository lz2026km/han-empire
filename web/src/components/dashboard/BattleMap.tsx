// ============================================
// 汉献帝之末路 v3.0 — 战势图 BattleMap
// 13 州简图 + 势力颜色, 蓝调极简风
// ============================================

import React from 'react';

export interface ProvinceState {
  id: string;
  name: string;
  faction: 'han' | 'caowei' | 'shuhan' | 'dongwu' | 'other';
  military: number;     // 0-100
  loyalty: number;      // 0-100
}

const FACTION_COLORS: Record<ProvinceState['faction'], { fill: string; stroke: string }> = {
  han:     { fill: '#3b82f6', stroke: '#60a5fa' },
  caowei:  { fill: '#6b7280', stroke: '#9ca3af' },
  shuhan:  { fill: '#10b981', stroke: '#34d399' },
  dongwu:  { fill: '#f59e0b', stroke: '#fbbf24' },
  other:   { fill: '#374151', stroke: '#4b5563' },
};

const FACTION_LABELS: Record<ProvinceState['faction'], string> = {
  han: '汉室', caowei: '曹魏', shuhan: '蜀汉', dongwu: '东吴', other: '其他',
};

export interface BattleMapProps {
  provinces: ProvinceState[];
  width?: number;
  height?: number;
  onSelect?: (id: string) => void;
}

// 13 州 简化坐标 (相对位置)
const PROVINCE_POS: Record<string, { x: number; y: number; r: number; label: string }> = {
  sili:    { x: 0.55, y: 0.42, r: 8, label: '司隶' },
  youzhou: { x: 0.78, y: 0.18, r: 9, label: '幽州' },
  jizhou:  { x: 0.66, y: 0.32, r: 9, label: '冀州' },
  bingzhou: { x: 0.55, y: 0.22, r: 7, label: '并州' },
  yanzhou: { x: 0.66, y: 0.50, r: 7, label: '兖州' },
  qingzhou: { x: 0.78, y: 0.38, r: 7, label: '青州' },
  xuzhou:  { x: 0.78, y: 0.55, r: 7, label: '徐州' },
  yuzhou:  { x: 0.55, y: 0.60, r: 6, label: '豫州' },
  jingzhou: { x: 0.45, y: 0.72, r: 8, label: '荆州' },
  yangzhou: { x: 0.74, y: 0.72, r: 9, label: '扬州' },
  yizhou:  { x: 0.30, y: 0.75, r: 10, label: '益州' },
  liangzhou: { x: 0.30, y: 0.45, r: 9, label: '凉州' },
  jiaozhou: { x: 0.60, y: 0.92, r: 6, label: '交州' },
};

export function BattleMap({
  provinces,
  width = 560,
  height = 380,
  onSelect,
}: BattleMapProps) {
  const factions = Array.from(new Set(provinces.map(p => p.faction)));

  return (
    <div style={{
      background: '#10101a',
      border: '1px solid #1f1f2a',
      borderRadius: 8,
      padding: 12,
    }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ display: 'block' }}>
        <defs>
          <linearGradient id="map-bg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#0a0a0f" />
            <stop offset="100%" stopColor="#15151f" />
          </linearGradient>
          <pattern id="map-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.02)" strokeWidth="1" />
          </pattern>
        </defs>

        {/* 背景 + 网格 */}
        <rect width={width} height={height} fill="url(#map-bg)" />
        <rect width={width} height={height} fill="url(#map-grid)" />

        {/* 州 */}
        {provinces.map(p => {
          const pos = PROVINCE_POS[p.id];
          if (!pos) return null;
          const cx = pos.x * width;
          const cy = pos.y * height;
          const r = pos.r + (p.military / 100) * 6;
          const colors = FACTION_COLORS[p.faction];
          return (
            <g key={p.id} style={{ cursor: onSelect ? 'pointer' : 'default' }} onClick={() => onSelect?.(p.id)}>
              <circle cx={cx} cy={cy} r={r + 4} fill={colors.stroke} opacity={0.15} />
              <circle
                cx={cx}
                cy={cy}
                r={r}
                fill={colors.fill}
                opacity={0.4 + (p.loyalty / 100) * 0.5}
                stroke={colors.stroke}
                strokeWidth={1.5}
              />
              <text
                x={cx}
                y={cy + 1}
                textAnchor="middle"
                dominantBaseline="central"
                fill="#fff"
                fontSize={9}
                fontWeight={500}
                pointerEvents="none"
              >
                {pos.label}
              </text>
            </g>
          );
        })}

        {/* 图例 */}
        <g transform={`translate(8 ${height - 12 * factions.length - 8})`}>
          {factions.map((f, i) => (
            <g key={f} transform={`translate(0 ${i * 14})`}>
              <circle cx={6} cy={6} r={4} fill={FACTION_COLORS[f].fill} stroke={FACTION_COLORS[f].stroke} />
              <text x={16} y={9} fill="#9ca3af" fontSize={10}>{FACTION_LABELS[f]}</text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
}

export default BattleMap;
