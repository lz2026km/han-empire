// v5.0 P0-3: Token 实时仪表盘组件
// 嵌入 court 主面板右上角, 显示 token 用量 + 缓存命中率 + 按 model 拆分
import { useEffect, useState } from 'react';
import './TokenStatsWidget.css';

interface ModelUsage {
  model: string;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  calls: number;
}

interface UsageStats {
  today: number;
  week: number;
  month: number;
  cost: number;
  currency: string;
  rate_per_million: number;
  by_model: ModelUsage[];
  by_purpose: Array<{ purpose: string; total_tokens: number; calls: number }>;
  total_calls: number;
}

interface CacheStats {
  total_calls: number;
  cache_hits: number;
  cache_misses: number;
  hit_rate: string;
  by_purpose: Record<string, { hits: number; misses: number }>;
}

interface TokenStats {
  usage: UsageStats;
  cache: CacheStats;
  savings: { estimated_saved_tokens: number; estimated_saved_usd: number };
  tier_config: Record<string, { base_url: string; model: string }>;
}

export function TokenStatsWidget({ refreshIntervalSec = 30 }: { refreshIntervalSec?: number }) {
  const [stats, setStats] = useState<TokenStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const fetchStats = async () => {
      try {
        const resp = await fetch('/api/token_stats');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        if (!cancelled) {
          setStats(data);
          setError(null);
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(e?.message || 'fetch failed');
        }
      }
    };

    fetchStats();
    const timer = setInterval(fetchStats, refreshIntervalSec * 1000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [refreshIntervalSec]);

  if (error) {
    return (
      <div className="token-stats-widget token-stats-error" title={error}>
        <span>Token 监控离线</span>
      </div>
    );
  }

  if (!stats) {
    return <div className="token-stats-widget">加载中...</div>;
  }

  const { usage, cache, savings, tier_config } = stats;
  const hitRatePct = cache.hit_rate || '0%';

  return (
    <div className="token-stats-widget" onClick={() => setExpanded(!expanded)}>
      <div className="token-stats-header">
        <span className="token-stats-label">Token 仪表盘</span>
        <span className="token-stats-month">本月 {usage.month.toLocaleString()}</span>
      </div>
      <div className="token-stats-row">
        <span className="token-stats-cell">
          <span className="cell-label">今</span>
          <span className="cell-value">{usage.today.toLocaleString()}</span>
        </span>
        <span className="token-stats-cell">
          <span className="cell-label">周</span>
          <span className="cell-value">{usage.week.toLocaleString()}</span>
        </span>
        <span className="token-stats-cell">
          <span className="cell-label">月</span>
          <span className="cell-value">{usage.month.toLocaleString()}</span>
        </span>
        <span className="token-stats-cell">
          <span className="cell-label">费</span>
          <span className="cell-value">${usage.cost.toFixed(2)}</span>
        </span>
        <span className="token-stats-cell" title="缓存命中率">
          <span className="cell-label">缓存</span>
          <span className="cell-value">{hitRatePct}</span>
        </span>
      </div>

      {expanded && (
        <div className="token-stats-detail">
          <h4>按 Model 拆分 (本月)</h4>
          {usage.by_model.length === 0 ? (
            <p className="empty-hint">本月暂无记录</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>模型</th>
                  <th>调用</th>
                  <th>Token</th>
                </tr>
              </thead>
              <tbody>
                {usage.by_model.map((m) => (
                  <tr key={m.model}>
                    <td className="model-name">{m.model}</td>
                    <td>{m.calls}</td>
                    <td>{m.total_tokens.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h4>按用途拆分 (本月)</h4>
          {usage.by_purpose.length === 0 ? (
            <p className="empty-hint">本月暂无记录</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>用途</th>
                  <th>调用</th>
                  <th>Token</th>
                </tr>
              </thead>
              <tbody>
                {usage.by_purpose.map((p) => (
                  <tr key={p.purpose}>
                    <td className="purpose-name">{p.purpose}</td>
                    <td>{p.calls}</td>
                    <td>{p.total_tokens.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h4>当前 4 Tier 配置</h4>
          <table>
            <thead>
              <tr>
                <th>Tier</th>
                <th>Model</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(tier_config).map(([tier, cfg]) => (
                <tr key={tier}>
                  <td className="tier-name">{tier}</td>
                  <td className="model-name">{cfg.model}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <p className="cache-savings">
            缓存节省: {savings.estimated_saved_tokens.toLocaleString()} tokens (${savings.estimated_saved_usd.toFixed(2)})
          </p>
        </div>
      )}

      <div className="token-stats-footer">
        <span>{usage.total_calls} 次调用</span>
        <span>•</span>
        <span>30s 自动刷新</span>
      </div>
    </div>
  );
}

export default TokenStatsWidget;
