// ============================================
// 汉献帝之末路 v3.2 — 存档槽位 UI
// 10 槽 + 自动存档列表 + 命名/删除
// ============================================

import React, { useEffect, useState } from 'react';

interface SaveSlot {
  slot_id: string;
  name: string;
  turn: number;
  campaign_id: string;
  created_at: number;
  updated_at: number;
  game_year: string;
  file_path: string;
}

interface Props {
  campaignId?: string;
  onLoad?: (slot: SaveSlot) => void;
  onSave?: (slotId: number, name: string) => void;
}

export const SaveSlots: React.FC<Props> = ({ campaignId = 'default', onLoad, onSave }) => {
  const [manualSlots, setManualSlots] = useState<SaveSlot[]>([]);
  const [autoSlots, setAutoSlots] = useState<SaveSlot[]>([]);
  const [loading, setLoading] = useState(true);

  const loadSlots = async () => {
    setLoading(true);
    try {
      // 列出 10 个手动槽
      const slots: SaveSlot[] = [];
      for (let i = 0; i < 10; i++) {
        try {
          const r = await fetch(`/api/saves/meta?campaign_id=${campaignId}&slot=${i}`);
          const d = await r.json();
          if (d.ok && d.meta) {
            slots.push({
              slot_id: String(i),
              name: d.meta.name || `存档 ${i}`,
              turn: d.meta.turn || 0,
              campaign_id: campaignId,
              created_at: d.meta.created_at || 0,
              updated_at: d.meta.updated_at || 0,
              game_year: d.meta.game_year || '',
              file_path: '',
            });
          } else {
            slots.push({
              slot_id: String(i),
              name: `空槽 ${i}`,
              turn: 0,
              campaign_id: campaignId,
              created_at: 0,
              updated_at: 0,
              game_year: '',
              file_path: '',
            });
          }
        } catch {
          slots.push({
            slot_id: String(i), name: `空槽 ${i}`, turn: 0, campaign_id: campaignId,
            created_at: 0, updated_at: 0, game_year: '', file_path: '',
          });
        }
      }
      setManualSlots(slots);
      // 自动存档
      const r2 = await fetch(`/api/auto-save/list?campaign_id=${campaignId}`);
      const d2 = await r2.json();
      if (d2.ok) setAutoSlots(d2.saves);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadSlots(); }, [campaignId]);

  const handleSave = async (slotId: number) => {
    const name = prompt('存档名称:', `存档 ${new Date().toLocaleString('zh-CN')}`);
    if (!name) return;
    try {
      const r = await fetch('/api/saves/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaign_id: campaignId, slot: slotId, name }),
      });
      const d = await r.json();
      if (d.ok) {
        onSave?.(slotId, name);
        loadSlots();
      } else {
        alert(d.error || '存档失败');
      }
    } catch (e) {
      alert('存档失败: ' + e);
    }
  };

  const handleLoad = (slot: SaveSlot) => {
    if (slot.turn === 0) return;
    onLoad?.(slot);
  };

  const handleDelete = async (slot: SaveSlot) => {
    if (!confirm(`确认删除「${slot.name}」?`)) return;
    try {
      const r = await fetch(`/api/saves/delete?campaign_id=${campaignId}&slot=${slot.slot_id}`, {
        method: 'POST',
      });
      const d = await r.json();
      if (d.ok) loadSlots();
    } catch (e) {
      alert('删除失败: ' + e);
    }
  };

  if (loading) return <div className="save-slots loading">加载存档...</div>;

  return (
    <div className="save-slots">
      <h2>存档管理</h2>

      <div className="slots-section">
        <h3>手动存档 (10 槽)</h3>
        <div className="slots-grid">
          {manualSlots.map(slot => (
            <div key={slot.slot_id}
                 className={`slot ${slot.turn === 0 ? 'empty' : 'filled'}`}
                 onClick={() => handleLoad(slot)} role="button" tabIndex={0}>
              <div className="slot-header">
                <span className="slot-id">#{slot.slot_id}</span>
                <span className="slot-turn">{slot.turn > 0 ? `回合 ${slot.turn}` : '空'}</span>
              </div>
              <div className="slot-name">{slot.name}</div>
              {slot.game_year && <div className="slot-year">{slot.game_year}</div>}
              <div className="slot-actions" onClick={e => e.stopPropagation()} role="button" tabIndex={0}>
                <button type="button" className="btn-save" onClick={() => handleSave(parseInt(slot.slot_id))}>
                  {slot.turn > 0 ? '覆盖' : '存档'}
                </button>
                {slot.turn > 0 && (
                  <button type="button" className="btn-delete" onClick={() => handleDelete(slot)}>删除</button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="slots-section">
        <h3>自动存档 (保留最近 3 个)</h3>
        {autoSlots.length === 0 ? (
          <div className="empty">尚无自动存档</div>
        ) : (
          <div className="auto-list">
            {autoSlots.map(s => (
              <div key={s.slot_id} className="auto-slot" onClick={() => handleLoad(s)} role="button" tabIndex={0}>
                <span className="auto-name">{s.name}</span>
                <span className="auto-year">{s.game_year}</span>
                <span className="auto-time">{new Date(s.created_at * 1000).toLocaleString('zh-CN')}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SaveSlots;
