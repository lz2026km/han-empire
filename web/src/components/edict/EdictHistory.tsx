// ============================================
// 汉献帝之末路 v2.5.0 — 旨意历史时间线 EdictHistory
// 状态色 (待/已/弹) + 可滚动
// ============================================

import React from 'react';
import './EdictHistory.css';

export type EdictStatus = 'draft' | 'issued' | 'executed' | 'rejected';

export interface EdictRecord {
  id: string;
  title: string;
  authority: number;     // 1-5
  status: EdictStatus;
  date: string;          // 年-月
  executor?: string;
}

export interface EdictHistoryProps {
  records?: EdictRecord[];
  onSelect?: (r: EdictRecord) => void;
}

const STATUS_CONFIG: Record<EdictStatus, { label: string; color: string }> = {
  draft: { label: '草稿', color: '#f59e0b' },
  issued: { label: '已颁', color: '#3b82f6' },
  executed: { label: '已执行', color: '#10b981' },
  rejected: { label: '已驳', color: '#ef4444' },
};

const AUTH_NAMES = ['', '口谕', '谕旨', '圣旨', '密旨', '廷议'];

const DEMO: EdictRecord[] = [
  { id: '1', title: '冀州赈济', authority: 3, status: 'executed', date: '189-03', executor: '曹操' },
  { id: '2', title: '兴修水利', authority: 2, status: 'issued', date: '189-04', executor: '孙坚' },
  { id: '3', title: '调兵徐州', authority: 4, status: 'draft', date: '189-05' },
  { id: '4', title: '任免韩馥', authority: 5, status: 'rejected', date: '189-02' },
];

export const EdictHistory: React.FC<EdictHistoryProps> = ({
  records = DEMO,
  onSelect,
}) => {
  return (
    <div className="edict-history">
      <div className="edict-history-title imperial">起居注</div>
      <div className="edict-history-list">
        {records.map((r) => {
          const s = STATUS_CONFIG[r.status];
          return (
            <div
              key={r.id}
              className="edict-history-item"
              onClick={() => onSelect?.(r)}
              role="button"
              tabIndex={0}
            >
              <div className="edict-history-time">{r.date}</div>
              <div className="edict-history-line" style={{ borderColor: s.color }}>
                <div
                  className="edict-history-dot"
                  style={{ background: s.color, boxShadow: `0 0 8px ${s.color}` }}
                />
              </div>
              <div className="edict-history-content">
                <div className="edict-history-head">
                  <span className="edict-history-record-title">{r.title}</span>
                  <span className="edict-history-authority" title={AUTH_NAMES[r.authority]}>
                    {AUTH_NAMES[r.authority]}
                  </span>
                </div>
                <div className="edict-history-meta">
                  <span style={{ color: s.color }}>{s.label}</span>
                  {r.executor && <span> · {r.executor}</span>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default EdictHistory;
