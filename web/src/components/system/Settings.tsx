// ============================================
// 汉献帝之末路 v3.0 — Settings 设置面板
// API Key (本地) / 模型选择 / Token 用量
// 蓝调极简风
// ============================================

import React, { useState, useEffect } from 'react';

const API_BASE = (typeof window !== 'undefined' && (window as any).__API_BASE__) || '';
const STORAGE_KEY = 'han_empire_api_keys';

export interface ApiKeyConfig {
  base_url: string;
  api_key: string;
  model: string;
}

const PROVIDERS = [
  { name: 'minimax', default_base: 'https://api.minimax.chat/v1', default_model: 'MiniMax-Text-01', label: 'MiniMax (主公默认)' },
  { name: 'qwen',    default_base: 'https://dashscope.aliyuncs.com/v1', default_model: 'qwen-plus', label: '通义千问 (阿里)' },
  { name: 'deepseek',default_base: 'https://api.deepseek.com/v1', default_model: 'deepseek-chat', label: 'DeepSeek' },
  { name: 'glm',     default_base: 'https://open.bigmodel.cn/api/paas/v4', default_model: 'glm-4-plus', label: '智谱 GLM-5' },
  { name: 'openai',  default_base: 'https://api.openai.com/v1', default_model: 'gpt-4o-mini', label: 'OpenAI' },
];

export function Settings() {
  const [provider, setProvider] = useState('minimax');
  const [cfg, setCfg] = useState<ApiKeyConfig>({
    base_url: PROVIDERS[0].default_base,
    api_key: '',
    model: PROVIDERS[0].default_model,
  });
  const [mode, setMode] = useState<'local' | 'server' | 'hybrid'>('server');
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'fail'>('idle');
  const [testMsg, setTestMsg] = useState<string>('');
  const [usage, setUsage] = useState<{ today: number; week: number; month: number; cost: number } | null>(null);

  // 加载本地 Key
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const saved = JSON.parse(raw) as { provider: string; cfg: ApiKeyConfig; mode: string };
        setProvider(saved.provider || 'minimax');
        setCfg(saved.cfg);
        setMode((saved.mode as any) || 'server');
      }
    } catch (e) { /* ignore */ }
  }, []);

  // provider 切换自动填默认值
  useEffect(() => {
    const p = PROVIDERS.find(p => p.name === provider);
    if (p) {
      setCfg(c => ({
        base_url: c.base_url && c.api_key ? c.base_url : p.default_base,
        api_key: c.api_key,
        model: c.model && c.api_key ? c.model : p.default_model,
      }));
    }
  }, [provider]);

  const save = () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ provider, cfg, mode }));
    alert('已保存到本地 (LocalStorage, 不上传)');
  };

  const test = async () => {
    setTestStatus('testing');
    setTestMsg('');
    try {
      const resp = await fetch(`${API_BASE}/api/llm/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode, provider, ...cfg }),
      });
      const data = await resp.json();
      if (data.ok) {
        setTestStatus('success');
        setTestMsg(data.message || '连通成功');
      } else {
        setTestStatus('fail');
        setTestMsg(data.error || '连通失败');
      }
    } catch (e: any) {
      setTestStatus('fail');
      setTestMsg(e.message || '请求失败');
    }
  };

  const fetchUsage = async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/usage/stats`);
      const data = await resp.json();
      setUsage(data);
    } catch (e) {
      // 静默
    }
  };

  useEffect(() => { fetchUsage(); }, []);

  const sectionStyle: React.CSSProperties = {
    background: '#10101a',
    border: '1px solid #1f1f2a',
    borderRadius: 8,
    padding: 16,
    marginBottom: 14,
  };
  const labelStyle: React.CSSProperties = {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 4,
    display: 'block',
  };
  const inputStyle: React.CSSProperties = {
    width: '100%',
    background: '#15151f',
    border: '1px solid #2a2a3a',
    color: '#e8e8ea',
    padding: '8px 10px',
    borderRadius: 4,
    fontSize: 13,
    outline: 'none',
  };

  return (
    <div style={{ padding: 20, maxWidth: 720, margin: '0 auto' }}>
      <h2 style={{ color: '#e8e8ea', fontSize: 20, marginBottom: 16 }}>⚙️ 设置</h2>

      {/* API Key 路由模式 */}
      <div style={sectionStyle}>
        <h3 style={{ fontSize: 14, marginBottom: 12, color: '#3b82f6' }}>🔑 API Key 路由模式</h3>
        <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
          {[
            { v: 'local',  l: '本地 (推荐)', d: '你的 Key 不上传' },
            { v: 'server', l: '服务端代理',  d: '用主公兜底 Key' },
            { v: 'hybrid', l: '混合',         d: '关键决策走本地' },
          ].map(o => (
            <button
              key={o.v}
              onClick={() => setMode(o.v as any)}
              style={{
                flex: 1,
                background: mode === o.v ? '#3b82f6' : '#15151f',
                border: '1px solid ' + (mode === o.v ? '#3b82f6' : '#2a2a3a'),
                color: '#fff',
                padding: 10,
                borderRadius: 6,
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <div style={{ fontWeight: 600, fontSize: 13 }}>{o.l}</div>
              <div style={{ fontSize: 11, color: mode === o.v ? '#dbeafe' : '#6b7280' }}>{o.d}</div>
            </button>
          ))}
        </div>
        <div style={{ fontSize: 11, color: '#6b7280', lineHeight: 1.5 }}>
          💡 本地模式: Key 存浏览器 LocalStorage, 不发给服务器 (青干《崇祯模拟器》官方要求)
        </div>
      </div>

      {/* 模型 Provider */}
      <div style={sectionStyle}>
        <h3 style={{ fontSize: 14, marginBottom: 12, color: '#3b82f6' }}>🤖 模型 Provider</h3>
        <label style={labelStyle}>提供商</label>
        <select value={provider} onChange={e => setProvider(e.target.value)} style={{ ...inputStyle, marginBottom: 10 }}>
          {PROVIDERS.map(p => <option key={p.name} value={p.name}>{p.label}</option>)}
        </select>

        <label style={labelStyle}>Base URL</label>
        <input
          type="text"
          value={cfg.base_url}
          onChange={e => setCfg({ ...cfg, base_url: e.target.value })}
          style={{ ...inputStyle, marginBottom: 10 }}
        />

        <label style={labelStyle}>Model</label>
        <input
          type="text"
          value={cfg.model}
          onChange={e => setCfg({ ...cfg, model: e.target.value })}
          style={{ ...inputStyle, marginBottom: 10 }}
        />

        <label style={labelStyle}>API Key (本地模式必填, server 模式忽略)</label>
        <input
          type="password"
          value={cfg.api_key}
          onChange={e => setCfg({ ...cfg, api_key: e.target.value })}
          placeholder="sk-..."
          style={{ ...inputStyle, marginBottom: 12 }}
        />

        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={save}
            style={{
              background: '#3b82f6', border: 'none', color: '#fff',
              padding: '8px 16px', borderRadius: 4, cursor: 'pointer', fontSize: 13,
            }}
          >
            💾 保存
          </button>
          <button
            onClick={test}
            disabled={testStatus === 'testing'}
            style={{
              background: 'transparent', border: '1px solid #3b82f6', color: '#3b82f6',
              padding: '8px 16px', borderRadius: 4,
              cursor: testStatus === 'testing' ? 'wait' : 'pointer', fontSize: 13,
            }}
          >
            {testStatus === 'testing' ? '测试中...' : '🔌 测试连通'}
          </button>
        </div>

        {testStatus === 'success' && (
          <div style={{ marginTop: 10, padding: 8, background: 'rgba(16,185,129,0.1)', border: '1px solid #10b981', borderRadius: 4, color: '#10b981', fontSize: 12 }}>
            ✅ {testMsg}
          </div>
        )}
        {testStatus === 'fail' && (
          <div style={{ marginTop: 10, padding: 8, background: 'rgba(239,68,68,0.1)', border: '1px solid #ef4444', borderRadius: 4, color: '#ef4444', fontSize: 12 }}>
            ❌ {testMsg}
          </div>
        )}
      </div>

      {/* Token 用量 */}
      <div style={sectionStyle}>
        <h3 style={{ fontSize: 14, marginBottom: 12, color: '#3b82f6' }}>📊 Token 用量</h3>
        {usage ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
            <Stat label="今日" value={usage.today} suffix="tokens" />
            <Stat label="本周" value={usage.week} suffix="tokens" />
            <Stat label="本月" value={usage.month} suffix="tokens" />
            <Stat label="估算成本" value={usage.cost} suffix="USD" fullWidth />
          </div>
        ) : (
          <div style={{ color: '#6b7280', fontSize: 12 }}>暂无数据 (W4 阶段四接入后会显示)</div>
        )}
        <button
          onClick={fetchUsage}
          style={{
            marginTop: 12, background: 'transparent', border: '1px solid #2a2a3a',
            color: '#9ca3af', padding: '6px 12px', borderRadius: 4, cursor: 'pointer', fontSize: 12,
          }}
        >
          🔄 刷新
        </button>
      </div>
    </div>
  );
}

function Stat({ label, value, suffix, fullWidth }: { label: string; value: number; suffix: string; fullWidth?: boolean }) {
  return (
    <div style={{
      background: '#15151f',
      border: '1px solid #2a2a3a',
      borderRadius: 6,
      padding: 12,
      gridColumn: fullWidth ? '1 / -1' : 'auto',
    }}>
      <div style={{ fontSize: 11, color: '#6b7280' }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 600, color: '#e8e8ea', marginTop: 4 }}>
        {typeof value === 'number' ? value.toLocaleString() : value}
        <span style={{ fontSize: 11, color: '#6b7280', marginLeft: 4 }}>{suffix}</span>
      </div>
    </div>
  );
}

export default Settings;
