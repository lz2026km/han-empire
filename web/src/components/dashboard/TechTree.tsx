// ============================================
// 汉献帝之末路 v3.1 — 科技树可视化
// 3 主线 (农本/王权/军备) × 5 节点 DAG
// 主色 #3b82f6, 1920×1080 锁死, 零 emoji
// ============================================

import React, { useEffect, useState } from 'react';

export interface TechNode {
  id: string;
  name: string;
  line: string;
  tier: number;
  cost: number;
  description: string;
  effects: Record<string, number>;
  prerequisites: string[];
  unlocks: string[];
  status: 'unlocked' | 'available' | 'locked';
}

export interface TechTreeData {
  nodes: TechNode[];
  reputation: number;
  lines: string[];
}

const LINE_COLORS: Record<string, string> = {
  '农本': '#10b981',
  '王权': '#3b82f6',
  '军备': '#ef4444',
};

const STATUS_COLORS = {
  unlocked: '#3b82f6',
  available: '#10b981',
  locked: '#6b7280',
};

interface Props {
  sessionId?: string;
  onUnlock?: (nodeId: string) => void;
}

export const TechTree: React.FC<Props> = ({ sessionId = 'default', onUnlock }) => {
  const [data, setData] = useState<TechTreeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<TechNode | null>(null);

  const loadTree = async () => {
    setLoading(true);
    try {
      const r = await fetch(`/api/tech-tree?session_id=${sessionId}`);
      const d = await r.json();
      if (d.ok) setData(d.tree);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadTree(); }, [sessionId]);

  const handleUnlock = async (nodeId: string) => {
    const r = await fetch('/api/tech-tree/unlock', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, node_id: nodeId }),
    });
    const d = await r.json();
    if (d.ok) {
      onUnlock?.(nodeId);
      loadTree();
    } else {
      alert(d.reason || '解锁失败');
    }
  };

  if (loading || !data) return <div className="tech-tree loading">加载科技树...</div>;

  // 按 tier 分组
  const tiers: TechNode[][] = [[], [], [], [], []];
  data.nodes.forEach(n => tiers[n.tier]?.push(n));

  return (
    <div className="tech-tree">
      <div className="tech-tree-header">
        <h2>科技树</h2>
        <div className="reputation">
          声望: <span className="value">{data.reputation}</span>
        </div>
      </div>

      <div className="tech-tree-legend">
        {data.lines.map(line => (
          <div key={line} className="legend-item">
            <span className="dot" style={{ background: LINE_COLORS[line] }} />
            {line}线
          </div>
        ))}
        <div className="legend-item"><span className="dot" style={{ background: STATUS_COLORS.unlocked }} />已解锁</div>
        <div className="legend-item"><span className="dot" style={{ background: STATUS_COLORS.available }} />可解锁</div>
        <div className="legend-item"><span className="dot" style={{ background: STATUS_COLORS.locked }} />未解锁</div>
      </div>

      <div className="tech-tree-grid">
        {tiers.map((tierNodes, tier) => (
          <div key={tier} className="tier-column">
            <div className="tier-label">第 {tier} 层</div>
            {tierNodes.map(node => {
              const color = LINE_COLORS[node.line] || '#3b82f6';
              const statusColor = STATUS_COLORS[node.status];
              return (
                <div
                  key={node.id}
                  className={`tech-node ${node.status}`}
                  style={{ borderColor: statusColor }}
                  onClick={() => setSelected(node)}
                >
                  <div className="node-name" style={{ color }}>{node.name}</div>
                  <div className="node-cost">声望 {node.cost}</div>
                  {node.status === 'available' && (
                    <button
                      className="unlock-btn"
                      onClick={(e) => { e.stopPropagation(); handleUnlock(node.id); }}
                      disabled={data.reputation < node.cost}
                    >
                      解锁
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      {selected && (
        <div className="tech-detail-panel">
          <h3>{selected.name} <span style={{ color: LINE_COLORS[selected.line] }}>· {selected.line}</span></h3>
          <p>{selected.description}</p>
          <div className="effects-list">
            <strong>效果:</strong>
            {Object.entries(selected.effects).map(([k, v]) => (
              <div key={k} className="effect-item">
                <span className="key">{k}</span>: <span className="val">{typeof v === 'number' && v < 5 ? `${(v * 100).toFixed(0)}%` : v}</span>
              </div>
            ))}
          </div>
          {selected.prerequisites.length > 0 && (
            <div className="prereq">
              <strong>前置:</strong> {selected.prerequisites.join(', ')}
            </div>
          )}
          <button className="close-btn" onClick={() => setSelected(null)}>关闭</button>
        </div>
      )}
    </div>
  );
};

export default TechTree;
