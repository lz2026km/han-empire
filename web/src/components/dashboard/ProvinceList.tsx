// ============================================
// 汉献帝之末路 v2.5.0 — 14 州郡列表 ProvinceList
// 所属派系色 + 民心/军心进度条
// ============================================

import React from 'react';
import './ProvinceList.css';

export interface Province {
  id: string;
  name: string;
  faction: string;     // 派系
  people: number;      // 民心 0-100
  army: number;        // 军心 0-100
  population: number;  // 人口 (万户)
}

export interface ProvinceListProps {
  provinces?: Province[];
  onSelect?: (p: Province) => void;
}

const FACTION_COLORS: Record<string, string> = {
  '主公': '#3b82f6',
  '汉室': '#3b82f6',
  '阉党': '#ef4444',
  '士族': '#f59e0b',
  '外戚': '#8b5cf6',
  '中立': '#64748b',
};

const DEMO_PROVINCES: Province[] = [
  { id: 'jizhou', name: '冀州', faction: '士族', people: 75, army: 80, population: 130 },
  { id: 'yanzhou', name: '兖州', faction: '主公', people: 82, army: 85, population: 90 },
  { id: 'yuzhou', name: '豫州', faction: '主公', people: 78, army: 70, population: 110 },
  { id: 'jingzhou', name: '荆州', faction: '士族', people: 70, army: 75, population: 120 },
  { id: 'yangzhou', name: '扬州', faction: '主公', people: 65, army: 60, population: 100 },
  { id: 'xuzhou', name: '徐州', faction: '士族', people: 60, army: 55, population: 80 },
  { id: 'qingzhou', name: '青州', faction: '主公', people: 70, army: 65, population: 95 },
  { id: 'youzhou', name: '幽州', faction: '外戚', people: 55, army: 70, population: 75 },
];

export const ProvinceList: React.FC<ProvinceListProps> = ({
  provinces = DEMO_PROVINCES,
  onSelect,
}) => {
  return (
    <div className="province-list">
      <div className="province-list-title imperial">州郡</div>
      <div className="province-list-scroll">
        {provinces.map((p) => {
          const color = FACTION_COLORS[p.faction] || FACTION_COLORS['中立'];
          return (
            <div
              key={p.id}
              className="province-item"
              onClick={() => onSelect?.(p)}
              style={{ '--faction-color': color } as React.CSSProperties}
              role="button"
              tabIndex={0}
            >
              <div className="province-item-head">
                <span className="province-item-name">{p.name}</span>
                <span className="province-item-faction" style={{ color }}>
                  {p.faction}
                </span>
              </div>
              <div className="province-item-bars">
                <div className="province-item-bar">
                  <span className="province-item-label">民</span>
                  <div className="province-item-track">
                    <div
                      className="province-item-fill province-item-fill-people"
                      style={{ width: `${p.people}%` }}
                    />
                  </div>
                  <span className="province-item-value">{p.people}</span>
                </div>
                <div className="province-item-bar">
                  <span className="province-item-label">军</span>
                  <div className="province-item-track">
                    <div
                      className="province-item-fill province-item-fill-army"
                      style={{ width: `${p.army}%` }}
                    />
                  </div>
                  <span className="province-item-value">{p.army}</span>
                </div>
              </div>
              <div className="province-item-pop">
                {p.population} 万户
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ProvinceList;
