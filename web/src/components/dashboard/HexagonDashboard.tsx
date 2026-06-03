// ============================================
// 汉献帝之末路 v2.5.0 — 6 维国势雷达 HexagonDashboard
// 民忠 / 军心 / 国库 / 士族 / 阉党 / 外戚
// SVG 雷达 + 数字滚动 + 平滑变形
// ============================================

import React, { useEffect, useRef, useState } from 'react';
import './HexagonDashboard.css';

export interface HexStat {
  key: string;
  label: string;
  value: number;   // 0-100
  color: string;
}

export interface HexagonDashboardProps {
  stats?: HexStat[];
  size?: number;
  animated?: boolean;
}

const DEFAULT_STATS: HexStat[] = [
  { key: 'people', label: '民忠', value: 72, color: '#10b981' },
  { key: 'army', label: '军心', value: 65, color: '#3b82f6' },
  { key: 'treasury', label: '国库', value: 48, color: '#f59e0b' },
  { key: 'clan', label: '士族', value: 81, color: '#8b5cf6' },
  { key: 'eunuch', label: '阉党', value: 33, color: '#ef4444' },
  { key: 'consort', label: '外戚', value: 45, color: '#06b6d4' },
];

// 数字滚动 hook
function useAnimatedNumber(target: number, duration = 800) {
  const [value, setValue] = useState(0);
  const startRef = useRef(0);
  const rafRef = useRef(0);
  useEffect(() => {
    const start = startRef.current;
    const delta = target - start;
    const t0 = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - t0) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(start + delta * eased));
      if (t < 1) rafRef.current = requestAnimationFrame(tick);
      else startRef.current = target;
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);
  return value;
}

// 6 维 → 6 个极角 (从顶部开始顺时针)
function getHexPoints(values: number[], size: number, center: number) {
  const maxR = size * 0.42;
  return values.map((v, i) => {
    const angle = (-Math.PI / 2) + (i * 2 * Math.PI / 6); // -90° 起
    const r = (v / 100) * maxR;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
      lx: center + maxR * Math.cos(angle),
      ly: center + maxR * Math.sin(angle),
      angle,
    };
  });
}

export const HexagonDashboard: React.FC<HexagonDashboardProps> = ({
  stats = DEFAULT_STATS,
  size = 280,
  animated = true,
}) => {
  const values = stats.map((s) => s.value);
  const center = size / 2;
  const points = getHexPoints(values, size, center);
  const pathData = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z';

  // 网格层 (5 圈)
  const gridLevels = [0.2, 0.4, 0.6, 0.8, 1.0];

  return (
    <div className="hex-dashboard">
      <div className="hex-dashboard-title imperial">国势</div>
      <svg viewBox={`0 0 ${size} ${size}`} className="hex-dashboard-svg">
        {/* 网格 */}
        {gridLevels.map((g, i) => {
          const gridPoints = getHexPoints([100, 100, 100, 100, 100, 100], size, center)
            .map((p) => ({
              x: center + (p.x - center) * g,
              y: center + (p.y - center) * g,
            }));
          const gridPath = gridPoints.map((p, j) => `${j === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z';
          return (
            <path
              key={i}
              d={gridPath}
              fill="none"
              stroke="rgba(148, 163, 184, 0.15)"
              strokeWidth={i === 4 ? 1.5 : 0.5}
            />
          );
        })}

        {/* 轴线 */}
        {points.map((p, i) => (
          <line
            key={i}
            x1={center}
            y1={center}
            x2={p.lx}
            y2={p.ly}
            stroke="rgba(148, 163, 184, 0.15)"
            strokeWidth={0.5}
          />
        ))}

        {/* 数据区 */}
        <path
          d={pathData}
          fill="rgba(59, 130, 246, 0.25)"
          stroke="#3b82f6"
          strokeWidth={2}
          className={animated ? 'hex-dashboard-data-animated' : ''}
        />

        {/* 顶点 */}
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={4}
            fill={stats[i].color}
            stroke="#0a0a0d"
            strokeWidth={1.5}
            className="hex-dashboard-dot"
          />
        ))}

        {/* 标签 */}
        {points.map((p, i) => {
          const lx = center + (p.lx - center) * 1.15;
          const ly = center + (p.ly - center) * 1.15;
          return (
            <g key={i}>
              <text
                x={lx}
                y={ly - 4}
                textAnchor="middle"
                fontSize="11"
                fill={stats[i].color}
                fontWeight="600"
              >
                {stats[i].label}
              </text>
              <text
                x={lx}
                y={ly + 10}
                textAnchor="middle"
                fontSize="13"
                fill="#c9a84c"
                fontWeight="bold"
                className="hex-dashboard-value"
                data-target={stats[i].value}
              >
                {animated ? <HexNumber target={stats[i].value} /> : stats[i].value}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

// 数字滚动子组件
const HexNumber: React.FC<{ target: number }> = ({ target }) => {
  const v = useAnimatedNumber(target);
  return <>{v}</>;
};

export default HexagonDashboard;
