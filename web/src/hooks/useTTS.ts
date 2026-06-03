// ============================================
// 汉献帝之末路 v2.5.0 — TTS 播报模块
// 优先: 浏览器 Web Speech API (免费 0 依赖)
// 备用: 服务端 edge-tts (Python)
// ============================================

import { useCallback, useRef, useState } from 'react';

export type TTSProvider = 'browser' | 'edge';

export interface TTSOptions {
  provider?: TTSProvider;
  voice?: string;
  rate?: number;   // 0.5 - 2.0
  pitch?: number;  // 0.5 - 2.0
  volume?: number; // 0 - 1
}

export interface TTSHook {
  speak: (text: string, options?: TTSOptions) => Promise<void>;
  stop: () => void;
  speaking: boolean;
  supported: boolean;
}

export function useTTS(): TTSHook {
  const [speaking, setSpeaking] = useState(false);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window;

  const speak = useCallback(
    async (text: string, options: TTSOptions = {}) => {
      if (!text.trim()) return;
      const { provider = 'browser', rate = 0.9, pitch = 0.8, volume = 1, voice } = options;

      // === 优先: 浏览器 Web Speech API ===
      if (provider === 'browser' && supported) {
        // 取消上一段
        window.speechSynthesis.cancel();

        const utter = new SpeechSynthesisUtterance(text);
        utter.lang = 'zh-CN';
        utter.rate = rate;
        utter.pitch = pitch;
        utter.volume = volume;

        // 选中文语音
        if (voice) {
          const voices = window.speechSynthesis.getVoices();
          const v = voices.find((v) => v.name === voice || v.lang.startsWith('zh'));
          if (v) utter.voice = v;
        } else {
          const voices = window.speechSynthesis.getVoices();
          const zh = voices.find((v) => v.lang === 'zh-CN' || v.lang === 'zh');
          if (zh) utter.voice = zh;
        }

        utter.onstart = () => setSpeaking(true);
        utter.onend = () => setSpeaking(false);
        utter.onerror = () => setSpeaking(false);

        utteranceRef.current = utter;
        window.speechSynthesis.speak(utter);
        return;
      }

      // === 备用: edge-tts (需后端代理) ===
      try {
        setSpeaking(true);
        const res = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, voice: voice || 'zh-CN-YunjianNeural', rate, pitch }),
        });
        if (!res.ok) throw new Error(`TTS ${res.status}`);
        // 浏览器播放 base64 音频
        const { audio } = await res.json();
        if (audio) {
          const audioEl = new Audio(`data:audio/mp3;base64,${audio}`);
          audioEl.onended = () => setSpeaking(false);
          audioEl.onerror = () => setSpeaking(false);
          await audioEl.play();
        } else {
          setSpeaking(false);
        }
      } catch (e) {
        console.warn('edge-tts fallback failed:', e);
        setSpeaking(false);
      }
    },
    [supported]
  );

  const stop = useCallback(() => {
    if (supported) {
      window.speechSynthesis.cancel();
    }
    setSpeaking(false);
  }, [supported]);

  return { speak, stop, speaking, supported };
}

// === 预设语速 (汉代雅韵) ===
export const TTS_PRESETS = {
  memorial: { rate: 0.85, pitch: 0.8 },  // 奏折 (平稳)
  debate: { rate: 1.0, pitch: 0.9 },      // 大臣发言 (略快)
  verdict: { rate: 0.7, pitch: 0.7 },     // 回奏 (深沉)
  imperial: { rate: 0.75, pitch: 0.75 },  // 圣旨 (威压)
} as const;

export default useTTS;
