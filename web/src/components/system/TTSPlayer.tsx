// ============================================
// 汉献帝之末路 v3.0 — TTS 圣旨朗读面板 TTSPlayer
// 调后端 /api/tts, 蓝调极简风
// ============================================

import React, { useState } from 'react';

export interface TTSPlayerProps {
  text: string;
  voice?: string;        // 'zh-CN-YunjianNeural' etc
  autoPlay?: boolean;
  compact?: boolean;     // true = 浮动按钮 false = 完整面板
}

const VOICES = [
  { id: 'zh-CN-YunjianNeural', label: '云健 (男声威压)' },
  { id: 'zh-CN-YunxiNeural',   label: '云希 (男声温润)' },
  { id: 'zh-CN-YunyangNeural', label: '云扬 (男声新闻)' },
];

const API_BASE = (typeof window !== 'undefined' && (window as any).__API_BASE__) || '';

export function TTSPlayer({
  text,
  voice = 'zh-CN-YunjianNeural',
  autoPlay = false,
  compact = false,
}: TTSPlayerProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedVoice, setSelectedVoice] = useState(voice);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const handlePlay = async () => {
    if (!text.trim()) {
      setError('无文本可朗读');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice: selectedVoice, rate: 0, pitch: 0 }),
      });
      if (!resp.ok) {
        throw new Error(`TTS 接口 ${resp.status}`);
      }
      const data = await resp.json();
      if (data.audio) {
        // base64 → Blob → ObjectURL
        const bin = atob(data.audio);
        const arr = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
        const blob = new Blob([arr], { type: 'audio/mp3' });
        const url = URL.createObjectURL(blob);
        if (audioUrl) URL.revokeObjectURL(audioUrl);
        setAudioUrl(url);
        // 自动播放
        const audio = new Audio(url);
        audio.play().catch(() => setError('播放失败,请手动点击'));
      } else {
        throw new Error('响应无 audio 字段');
      }
    } catch (e: any) {
      setError(e.message || '朗读失败');
    } finally {
      setLoading(false);
    }
  };

  if (compact) {
    return (
      <button
        onClick={handlePlay}
        disabled={loading}
        style={{
          background: 'transparent',
          border: '1px solid #3b82f6',
          color: '#3b82f6',
          padding: '4px 10px',
          borderRadius: 4,
          cursor: loading ? 'wait' : 'pointer',
          fontSize: 12,
        }}
      >
        {loading ? '加载中' : '朗读'} 朗读
      </button>
    );
  }

  return (
    <div style={{
      background: '#10101a',
      border: '1px solid #1f1f2a',
      borderRadius: 8,
      padding: 14,
    }}>
      <div style={{ marginBottom: 10, fontSize: 13, fontWeight: 600, color: '#e8e8ea' }}>
         圣旨朗读
      </div>

      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10 }}>
        <select
          value={selectedVoice}
          onChange={e => setSelectedVoice(e.target.value)}
          style={{
            background: '#15151f',
            border: '1px solid #2a2a3a',
            color: '#e8e8ea',
            padding: '6px 10px',
            borderRadius: 4,
            fontSize: 12,
            flex: 1,
          }}
        >
          {VOICES.map(v => (
            <option key={v.id} value={v.id}>{v.label}</option>
          ))}
        </select>

        <button
          onClick={handlePlay}
          disabled={loading}
          style={{
            background: '#3b82f6',
            border: 'none',
            color: '#fff',
            padding: '6px 14px',
            borderRadius: 4,
            cursor: loading ? 'wait' : 'pointer',
            fontSize: 13,
            fontWeight: 500,
          }}
        >
          {loading ? '合成中...' : '▶ 朗读'}
        </button>
      </div>

      {error && (
        <div style={{ color: '#ef4444', fontSize: 12, marginBottom: 8 }}>[警告]  {error}</div>
      )}

      {audioUrl && (
        <audio
          src={audioUrl}
          controls
          autoPlay={autoPlay}
          style={{ width: '100%', height: 32 }}
        />
      )}

      <div style={{ fontSize: 11, color: '#6b7280', marginTop: 8, lineHeight: 1.4 }}>
        调用 /api/tts (edge-tts 微软免费中文语音合成)
      </div>
    </div>
  );
}

export default TTSPlayer;
