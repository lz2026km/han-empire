// ============================================
// 汉献帝之末路 v3.2 — Canvas DAG 渲染
// 节点 > 100 用 Canvas + 虚拟滚动 + LOD
// ============================================

import React, { useEffect, useRef, useState } from 'react';

interface DAGNode {
  id: string;
  name: string;
  line: string;
  tier: number;
  cost: number;
  status: 'unlocked' | 'available' | 'locked';
  x?: number;
  y?: number;
}

interface Props {
  sessionId?: string;
  useLOD?: boolean;
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

export const CanvasDAG: React.FC<Props> = ({ sessionId = 'default', useLOD = true }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [nodes, setNodes] = useState<DAGNode[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [fps, setFps] = useState(0);
  const [loading, setLoading] = useState(true);

  const loadDAG = async () => {
    setLoading(true);
    try {
      const r = await fetch('/api/dag/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, use_lod: useLOD, lod_threshold: 100 }),
      });
      const d = await r.json();
      if (d.ok) {
        // 自动布局: 按 tier × line 网格
        const layoutNodes = layoutDAG(d.nodes);
        setNodes(layoutNodes);
        setStats(d.stats);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadDAG(); }, [sessionId, useLOD]);

  // Canvas 渲染
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || nodes.length === 0) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 设置画布尺寸
    canvas.width = 1920;
    canvas.height = 1080;

    // FPS 监控
    let last = performance.now();
    let frames = 0;
    let raf = 0;

    const draw = () => {
      frames++;
      const now = performance.now();
      if (now - last >= 1000) {
        setFps(frames);
        frames = 0;
        last = now;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // 绘制连线 (按 tier 连接)
      ctx.strokeStyle = '#475569';
      ctx.lineWidth = 2;
      nodes.forEach(n => {
        // 简化: 同 line 内 tier 升序连接
        if (n.tier > 0) {
          const prev = nodes.find(p => p.line === n.line && p.tier === n.tier - 1);
          if (prev && prev.x !== undefined && prev.y !== undefined &&
              n.x !== undefined && n.y !== undefined) {
            ctx.beginPath();
            ctx.moveTo(prev.x, prev.y);
            ctx.lineTo(n.x, n.y);
            ctx.stroke();
          }
        }
      });

      // 绘制节点
      nodes.forEach(n => {
        if (n.x === undefined || n.y === undefined) return;
        const color = LINE_COLORS[n.line] || '#3b82f6';
        const statusColor = STATUS_COLORS[n.status];
        // 外圈
        ctx.fillStyle = statusColor;
        ctx.beginPath();
        ctx.arc(n.x, n.y, 28, 0, Math.PI * 2);
        ctx.fill();
        // 内圈
        ctx.fillStyle = '#0f172a';
        ctx.beginPath();
        ctx.arc(n.x, n.y, 22, 0, Math.PI * 2);
        ctx.fill();
        // 边框
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(n.x, n.y, 22, 0, Math.PI * 2);
        ctx.stroke();
        // 名称
        ctx.fillStyle = '#f1f5f9';
        ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(n.name, n.x, n.y + 45);
        // 费用
        ctx.fillStyle = '#94a3b8';
        ctx.font = '12px sans-serif';
        ctx.fillText(`声望 ${n.cost}`, n.x, n.y + 60);
      });

      raf = requestAnimationFrame(draw);
    };

    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [nodes]);

  if (loading) return <div className="canvas-dag loading">加载 Canvas DAG...</div>;

  return (
    <div className="canvas-dag">
      <div className="dag-stats">
        <span>节点: <strong>{nodes.length}</strong></span>
        <span>FPS: <strong className={fps < 30 ? 'low' : 'ok'}>{fps}</strong></span>
        {stats && <span>状态: {stats.by_status.unlocked}/{stats.by_status.available}/{stats.by_status.locked}</span>}
        <span>渲染: Canvas {useLOD && nodes.length > 100 ? '+ LOD' : ''}</span>
      </div>
      <canvas ref={canvasRef} className="dag-canvas" />
    </div>
  );
};

// 简易布局: 3 line × 5 tier 网格
function layoutDAG(nodes: any[]): DAGNode[] {
  const lines = ['农本', '王权', '军备'];
  const TIER_WIDTH = 360;
  const LINE_HEIGHT = 280;
  const START_X = 200;
  const START_Y = 150;
  return nodes.map(n => {
    const lineIdx = lines.indexOf(n.line);
    const tier = n.tier || 0;
    return {
      ...n,
      x: START_X + tier * TIER_WIDTH,
      y: START_Y + lineIdx * LINE_HEIGHT,
    };
  });
}

export default CanvasDAG;
