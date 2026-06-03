// ============================================
// 汉献帝之末路 v3.1 — 后果链 DAG 可视化
// 4 类型后果: 即时/短期/长期/永久
// 实色节点 (绿/蓝/橙/红), 零 emoji
// ============================================

import React, { useEffect, useState } from 'react';

export interface ConsequenceNode {
  id: string;
  decision_id: string;
  decision_type: string;
  description: string;
  type: 'immediate' | 'short' | 'long' | 'permanent';
  type_color: string;
  effects: Record<string, number>;
  target: string;
  created_at: number;
  expires_at: number | null;
  expired: boolean;
  depends_on: string[];
}

interface Props {
  sessionId?: string;
  turn?: number;
  onClose?: () => void;
}

export const ConsequenceChain: React.FC<Props> = ({ sessionId = 'default', turn = 0, onClose }) => {
  const [nodes, setNodes] = useState<ConsequenceNode[]>([]);
  const [typeLegend, setTypeLegend] = useState<Record<string, string>>({});
  const [typeColors, setTypeColors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  const loadChain = async () => {
    setLoading(true);
    try {
      const r = await fetch(`/api/consequence-chain?session_id=${sessionId}&turn=${turn}`);
      const d = await r.json();
      if (d.ok) {
        setNodes(d.chain.nodes);
        setTypeLegend(d.chain.type_legend);
        setTypeColors(d.chain.type_colors);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadChain(); }, [sessionId, turn]);

  // 按决策 ID 分组
  const byDecision: Record<string, ConsequenceNode[]> = {};
  nodes.forEach(n => {
    if (!byDecision[n.decision_id]) byDecision[n.decision_id] = [];
    byDecision[n.decision_id].push(n);
  });

  const filteredNodes = filter === 'all' ? nodes : nodes.filter(n => n.type === filter);

  if (loading) return <div className="consequence-chain loading">加载后果链...</div>;

  return (
    <div className="consequence-chain">
      <div className="chain-header">
        <h2>后果链 · 回合 {turn}</h2>
        {onClose && <button type="button" className="close-btn" onClick={onClose}>关闭</button>}
      </div>

      <div className="chain-legend">
        <div className="filter-group">
          <button type="button"
            className={filter === 'all' ? 'active' : ''}
            onClick={() => setFilter('all')}
          >
            全部 ({nodes.length})
          </button>
          {Object.entries(typeLegend).map(([type, label]) => (
            <button type="button"
              key={type}
              className={filter === type ? 'active' : ''}
              onClick={() => setFilter(type)}
              style={{ borderColor: typeColors[type] }}
            >
              {label} ({nodes.filter(n => n.type === type).length})
            </button>
          ))}
        </div>
      </div>

      <div className="chain-view">
        {Object.keys(byDecision).length === 0 ? (
          <div className="empty">暂无后果记录</div>
        ) : (
          Object.entries(byDecision).map(([decisionId, cNodes]) => (
            <div key={decisionId} className="decision-group">
              <div className="decision-header">
                <span className="decision-type">{cNodes[0]?.decision_type}</span>
                <span className="decision-id">{decisionId}</span>
              </div>
              <div className="consequence-nodes">
                {cNodes.filter(n => filter === 'all' || n.type === filter).map(node => (
                  <div
                    key={node.id}
                    className={`consequence-node ${node.expired ? 'expired' : ''}`}
                    style={{ borderColor: node.type_color, background: `${node.type_color}15` }}
                  >
                    <div className="node-type" style={{ background: node.type_color }}>
                      {typeLegend[node.type]}
                    </div>
                    <div className="node-desc">{node.description}</div>
                    <div className="node-target">范围: {node.target}</div>
                    {Object.keys(node.effects).length > 0 && (
                      <div className="node-effects">
                        {Object.entries(node.effects).map(([k, v]) => (
                          <span key={k} className={`effect ${v >= 0 ? 'pos' : 'neg'}`}>
                            {k} {v >= 0 ? '+' : ''}{(v * 100).toFixed(0)}%
                          </span>
                        ))}
                      </div>
                    )}
                    {node.expires_at && (
                      <div className="node-expire">
                        过期: 回合 {node.expires_at}
                        {node.expired && <span className="expired-mark">已过期</span>}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ConsequenceChain;
