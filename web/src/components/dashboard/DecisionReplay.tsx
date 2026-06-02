// ============================================
// 汉献帝之末路 v3.1 — 决策回放
// 时间线滑块控制, 可快进/回放所有决策
// ============================================

import React, { useEffect, useState, useRef } from 'react';

interface TimelineEntry {
  id: string;
  turn: number;
  game_year: string;
  decision_type: string;
  action: string;
  description: string;
  effects: Record<string, number>;
  consequence_count: number;
}

interface Stats {
  total: number;
  by_type: Record<string, number>;
  first_turn: number;
  last_turn: number;
}

interface Props {
  sessionId?: string;
}

export const DecisionReplay: React.FC<Props> = ({ sessionId = 'default' }) => {
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [currentTurn, setCurrentTurn] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [loading, setLoading] = useState(true);
  const timerRef = useRef<number | null>(null);

  const loadTimeline = async () => {
    setLoading(true);
    try {
      const r = await fetch(`/api/decision-log?session_id=${sessionId}`);
      const d = await r.json();
      if (d.ok) {
        setTimeline(d.timeline);
        setStats(d.stats);
        if (d.stats.last_turn > 0) setCurrentTurn(d.stats.first_turn);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadTimeline(); }, [sessionId]);

  // 自动播放
  useEffect(() => {
    if (!playing || !stats) return;
    timerRef.current = window.setInterval(() => {
      setCurrentTurn(t => {
        if (t >= stats.last_turn) {
          setPlaying(false);
          return t;
        }
        return t + 1;
      });
    }, 1500 / speed);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [playing, speed, stats]);

  if (loading) return <div className="decision-replay loading">加载决策日志...</div>;
  if (!stats || stats.total === 0) {
    return <div className="decision-replay empty">尚无决策记录</div>;
  }

  const turnEntries = timeline.filter(e => e.turn === currentTurn);
  const maxTurn = Math.max(stats.last_turn, 1);

  return (
    <div className="decision-replay">
      <div className="replay-header">
        <h2>决策回放</h2>
        <div className="replay-stats">
          <span>总决策: <strong>{stats.total}</strong></span>
          <span>回合: <strong>{currentTurn} / {stats.last_turn}</strong></span>
        </div>
      </div>

      <div className="replay-controls">
        <button type="button"
          className="play-btn"
          onClick={() => setPlaying(!playing)}
          disabled={currentTurn >= stats.last_turn && !playing}
        >
          {playing ? '暂停' : '播放'}
        </button>
        <button type="button"
          className="reset-btn"
          onClick={() => { setPlaying(false); setCurrentTurn(stats.first_turn); }}
        >
          重置
        </button>
        <div className="speed-control">
          <label>速度:</label>
          <select value={speed} onChange={e => setSpeed(Number(e.target.value))}>
            <option value="0.5">0.5×</option>
            <option value="1">1×</option>
            <option value="2">2×</option>
            <option value="4">4×</option>
          </select>
        </div>
        <input
          type="range"
          min={stats.first_turn}
          max={maxTurn}
          value={currentTurn}
          onChange={e => setCurrentTurn(Number(e.target.value))}
          className="timeline-slider"
        />
      </div>

      <div className="replay-content">
        {turnEntries.length === 0 ? (
          <div className="no-entries">回合 {currentTurn} 暂无决策</div>
        ) : (
          turnEntries.map(entry => (
            <div key={entry.id} className="replay-entry">
              <div className="entry-header">
                <span className="entry-type">{entry.decision_type}</span>
                <span className="entry-year">{entry.game_year || `回合 ${entry.turn}`}</span>
                {entry.consequence_count > 0 && (
                  <span className="entry-csq">{entry.consequence_count} 个后果</span>
                )}
              </div>
              <div className="entry-action">{entry.action}</div>
              <div className="entry-desc">{entry.description}</div>
              {Object.keys(entry.effects).length > 0 && (
                <div className="entry-effects">
                  {Object.entries(entry.effects).map(([k, v]) => (
                    <span key={k} className={`effect ${v >= 0 ? 'pos' : 'neg'}`}>
                      {k} {v >= 0 ? '+' : ''}{typeof v === 'number' && Math.abs(v) < 5 ? `${(v * 100).toFixed(0)}%` : v}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <div className="replay-by-type">
        <h4>决策类型分布</h4>
        {Object.entries(stats.by_type).map(([type, count]) => (
          <div key={type} className="type-bar">
            <span className="type-name">{type}</span>
            <div className="bar-bg">
              <div
                className="bar-fill"
                style={{ width: `${(count / stats.total) * 100}%` }}
              />
            </div>
            <span className="type-count">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DecisionReplay;
