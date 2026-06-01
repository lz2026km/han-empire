// ============================================
// 汉献帝之末路 v2.5.0 — 奏折收件箱 Inbox
// 4 类 (月/急/密/报) + 红点 + 筛选 (全/未读/已批/待批)
// ============================================

import React, { useState, useMemo } from 'react';
import { InboxItem } from './InboxItem';
import type { Memorial } from '../../types';
import './Inbox.css';

export type InboxFilter = 'all' | 'unread' | 'pending' | 'approved';
export type MemorialType = 'monthly' | 'urgent' | 'secret' | 'report';

const FILTERS: Array<{ key: InboxFilter; label: string }> = [
  { key: 'all', label: '全部' },
  { key: 'unread', label: '未读' },
  { key: 'pending', label: '待批' },
  { key: 'approved', label: '已批' },
];

export interface InboxProps {
  memorials?: Memorial[];
  onSelect?: (m: Memorial) => void;
  selectedId?: string;
}

export const Inbox: React.FC<InboxProps> = ({
  memorials = [],
  onSelect,
  selectedId,
}) => {
  const [filter, setFilter] = useState<InboxFilter>('all');

  const filtered = useMemo(() => {
    return memorials.filter((m) => {
      if (filter === 'all') return true;
      if (filter === 'unread') return !m.read;
      if (filter === 'pending') return m.status === 'pending';
      if (filter === 'approved') return m.status === 'approved';
      return true;
    });
  }, [memorials, filter]);

  const counts = useMemo(() => ({
    all: memorials.length,
    unread: memorials.filter((m) => !m.read).length,
    pending: memorials.filter((m) => m.status === 'pending').length,
    approved: memorials.filter((m) => m.status === 'approved').length,
  }), [memorials]);

  // 演示数据
  const demoMemorials: Memorial[] = memorials.length > 0 ? filtered : [
    {
      id: 'm1',
      type: 'urgent' as MemorialType,
      title: '冀州急报: 黄巾余党复起',
      author: '韩馥',
      date: '本月',
      read: false,
      status: 'pending',
      preview: '黄巾余党张角残部, 聚众三千, 烧毁邺城仓廪...',
    },
    {
      id: 'm2',
      type: 'monthly' as MemorialType,
      title: '豫州月奏: 麦收丰稔',
      author: '孙坚',
      date: '本月',
      read: true,
      status: 'pending',
      preview: '豫州今岁麦收, 比常年多三成, 仓廪充实...',
    },
    {
      id: 'm3',
      type: 'secret' as MemorialType,
      title: '密报: 袁绍私铸钱币',
      author: '密探',
      date: '本月',
      read: false,
      status: 'pending',
      preview: '袁本初于邺城私开铸坊, 日得钱五千...',
    },
    {
      id: 'm4',
      type: 'report' as MemorialType,
      title: '呈报: 司隶校尉履职',
      author: '曹操',
      date: '上月',
      read: true,
      status: 'approved',
      preview: '司隶校尉到任, 已点验洛阳防务...',
    },
  ].filter((m) => filter === 'all' || (
    (filter === 'unread' && !m.read) ||
    (filter === 'pending' && m.status === 'pending') ||
    (filter === 'approved' && m.status === 'approved')
  ));

  return (
    <div className="inbox">
      <div className="inbox-header">
        <h3 className="inbox-title imperial">奏折</h3>
        <div className="inbox-badge">
          {counts.unread > 0 && (
            <span className="inbox-badge-dot">{counts.unread}</span>
          )}
        </div>
      </div>

      <div className="inbox-filters">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            className={`inbox-filter ${filter === f.key ? 'inbox-filter-active' : ''}`}
            onClick={() => setFilter(f.key)}
          >
            {f.label}
            <span className="inbox-filter-count">
              {counts[f.key]}
            </span>
          </button>
        ))}
      </div>

      <div className="inbox-list">
        {demoMemorials.length === 0 ? (
          <div className="inbox-empty">
            <div className="inbox-empty-icon">📜</div>
            <div className="inbox-empty-text">奏折匣中空</div>
          </div>
        ) : (
          demoMemorials.map((m) => (
            <InboxItem
              key={m.id}
              memorial={m}
              selected={selectedId === m.id}
              onClick={() => onSelect?.(m)}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default Inbox;
