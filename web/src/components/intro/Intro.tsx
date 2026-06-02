// ============================================
// 汉献帝之末路 v2.5.0 — 启动动画 Intro
// 30s 三幕过场: 太极八卦 → 汉献帝登基 → 承明殿值房
// 可跳过 (Skip 按钮 + Esc/Space 快捷键)
// ============================================

import React, { useState, useEffect } from 'react';
import './Intro.css';

export interface IntroProps {
  onComplete: () => void;
  duration?: number; // 总时长 ms, 默认 30000
}

type Phase = 'taiji' | 'ascension' | 'chamber' | 'done';

const PHASE_DURATIONS: Record<Phase, number> = {
  taiji: 10000,      // 10s 太极八卦
  ascension: 10000,  // 10s 登基
  chamber: 10000,    // 10s 值房
  done: 0,
};

export const Intro: React.FC<IntroProps> = ({
  onComplete,
  duration = 30000,
}) => {
  const [phase, setPhase] = useState<Phase>('taiji');
  const [progress, setProgress] = useState(0);

  // === 阶段推进 ===
  useEffect(() => {
    const total = duration;
    const interval = setInterval(() => {
      setProgress((p) => {
        const next = p + 100;
        if (next >= total * 0.33 && phase === 'taiji') setPhase('ascension');
        else if (next >= total * 0.66 && phase === 'ascension') setPhase('chamber');
        else if (next >= total && phase === 'chamber') {
          setPhase('done');
          onComplete();
          clearInterval(interval);
        }
        return Math.min(next, total);
      });
    }, 100);
    return () => clearInterval(interval);
  }, [duration, phase, onComplete]);

  // === 跳过 ===
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape' || e.key === ' ') {
        onComplete();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onComplete]);

  if (phase === 'done') return null;

  return (
    <div className="intro" aria-label="启动动画">
      {/* === 幕 1: 太极八卦 === */}
      {phase === 'taiji' && (
        <div className="intro-phase intro-taiji">
          <svg viewBox="-100 -100 200 200" className="intro-taiji-svg">
            <defs>
              <radialGradient id="taiji-glow">
                <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.6" />
                <stop offset="100%" stopColor="#fbbf24" stopOpacity="0" />
              </radialGradient>
            </defs>
            <circle r="80" fill="url(#taiji-glow)" className="intro-taiji-glow" />
            <g className="intro-taiji-rotate">
              <path
                d="M 0,-70 A 70,70 0 0,1 0,70 A 35,35 0 0,1 0,0 A 35,35 0 0,0 0,-70 Z"
                fill="#1a1a22"
              />
              <path
                d="M 0,-70 A 70,70 0 0,0 0,70 A 35,35 0 0,0 0,0 A 35,35 0 0,1 0,-70 Z"
                fill="#f5f5f5"
              />
              <circle cy="-35" r="7" fill="#1a1a22" />
              <circle cy="35" r="7" fill="#f5f5f5" />
            </g>
            <g className="intro-bagua">
              {Array.from({ length: 8 }).map((_, i) => {
                const angle = (i * 45 * Math.PI) / 180;
                const x = Math.cos(angle) * 95;
                const y = Math.sin(angle) * 95;
                return (
                  <g key={i} transform={`translate(${x}, ${y})`}>
                    <circle r="6" fill="#c9a84c" opacity="0.8" />
                    <text
                      y="3"
                      textAnchor="middle"
                      fontSize="8"
                      fill="#0a0a0d"
                      fontWeight="bold"
                    >
                      {['乾', '兑', '离', '震', '巽', '坎', '艮', '坤'][i]}
                    </text>
                  </g>
                );
              })}
            </g>
          </svg>
          <div className="intro-subtitle">太初 · 混沌分阴阳</div>
        </div>
      )}

      {/* === 幕 2: 汉献帝登基 === */}
      {phase === 'ascension' && (
        <div className="intro-phase intro-ascension">
          <div className="intro-emperor-silhouette">
            <div className="intro-emperor-crown">冕</div>
            <div className="intro-emperor-body">汉</div>
          </div>
          <div className="intro-title">汉献帝 · 初平元年</div>
          <div className="intro-subtitle">承继大统 · 受命于天</div>
        </div>
      )}

      {/* === 幕 3: 承明殿值房 === */}
      {phase === 'chamber' && (
        <div className="intro-phase intro-chamber">
          <div className="intro-chamber-bg" />
          <div className="intro-title">承明殿值房</div>
          <div className="intro-subtitle">陛下理政 · 奏折候批</div>
        </div>
      )}

      {/* === 进度条 + 跳过 === */}
      <div className="intro-progress">
        <div
          className="intro-progress-bar"
          style={{ width: `${(progress / duration) * 100}%` }}
        />
      </div>
      <button type="button"
        className="intro-skip"
        onClick={onComplete}
        aria-label="跳过启动动画"
      >
        跳过 (Esc / Space)
      </button>
    </div>
  );
};

export default Intro;
