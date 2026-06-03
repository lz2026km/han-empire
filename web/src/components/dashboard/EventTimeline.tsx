// ============================================
// 汉献帝之末路 v3.0 — 大事年表 EventTimeline
// 按年份倒序, 蓝调极简风
// ============================================

import React from 'react';

export interface TimelineEvent {
  id: string;
  year: number;
  month?: number;
  title: string;
  summary: string;
  importance?: 1 | 2 | 3 | 4 | 5;  // 1=低 5=极高
  faction?: string;
}

export interface EventTimelineProps {
  events: TimelineEvent[];
  maxItems?: number;
  onSelect?: (id: string) => void;
}

const IMPORTANCE_COLORS = {
  1: '#6b7280',
  2: '#9ca3af',
  3: '#3b82f6',
  4: '#f59e0b',
  5: '#ef4444',
};

const MONTH_NAMES = ['', '正月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '腊月'];

export function EventTimeline({ events, maxItems = 30, onSelect }: EventTimelineProps) {
  const sorted = [...events]
    .sort((a, b) => b.year - a.year || (b.month || 0) - (a.month || 0))
    .slice(0, maxItems);

  if (sorted.length === 0) {
    return (
      <div style={{
        textAlign: 'center',
        color: '#6b7280',
        padding: 24,
        fontSize: 12,
        background: '#10101a',
        border: '1px solid #1f1f2a',
        borderRadius: 8,
      }}>
        暂无大事
      </div>
    );
  }

  return (
    <div style={{
      background: '#10101a',
      border: '1px solid #1f1f2a',
      borderRadius: 8,
      padding: 16,
      maxHeight: 500,
      overflowY: 'auto',
    }}>
      <div style={{ position: 'relative', paddingLeft: 20 }}>
        {/* 时间线竖线 */}
        <div style={{
          position: 'absolute',
          left: 7,
          top: 6,
          bottom: 6,
          width: 2,
          background: 'linear-gradient(180deg, #3b82f6 0%, transparent 100%)',
          opacity: 0.3,
        }} />

        {sorted.map(e => {
          const imp = e.importance || 3;
          const dotColor = IMPORTANCE_COLORS[imp];
          return (
            <div
              key={e.id}
              onClick={() => onSelect?.(e.id)}
              style={{
                position: 'relative',
                marginBottom: 14,
                paddingBottom: 4,
                cursor: onSelect ? 'pointer' : 'default',
              }}
            >
              {/* 圆点 */}
              <div style={{
                position: 'absolute',
                left: -18,
                top: 4,
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: dotColor,
                border: '2px solid #0a0a0f',
                boxShadow: `0 0 0 2px ${dotColor}30`,
              }} />

              <div style={{ fontSize: 12, color: dotColor, fontWeight: 600, marginBottom: 2 }}>
                建安{e.year - 196}年 {e.month ? MONTH_NAMES[e.month] : ''}
              </div>
              <div style={{ fontSize: 13, fontWeight: 500, color: '#e8e8ea', marginBottom: 2 }}>
                {e.title}
              </div>
              <div style={{ fontSize: 12, color: '#9ca3af', lineHeight: 1.4 }}>
                {e.summary}
              </div>
              {e.faction && (
                <span style={{
                  display: 'inline-block',
                  fontSize: 10,
                  color: '#6b7280',
                  border: '1px solid #2a2a3a',
                  borderRadius: 3,
                  padding: '1px 6px',
                  marginTop: 4,
                }}>
                  {e.faction}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default EventTimeline;
