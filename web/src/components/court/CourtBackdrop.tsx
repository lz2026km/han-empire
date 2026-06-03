// ============================================
// 汉献帝之末路 v2.5.0 — 4 套承明殿背景 CourtBackdrop
// 早 (辰) / 午 (午) / 昏 (酉) / 夜 (子)
// 烛火摇曳 + 窗外雨雪粒子
// ============================================

import React, { useEffect, useState } from 'react';
import './CourtBackdrop.css';

export type TimeOfDay = 'dawn' | 'noon' | 'dusk' | 'night';

export interface CourtBackdropProps {
  timeOfDay?: TimeOfDay;
  weather?: 'clear' | 'rain' | 'snow';
  showCandles?: boolean;
}

// 时辰→景别映射
const TIME_MAP: Record<TimeOfDay, { bg: string; window: string; candle: number }> = {
  dawn: {
    bg: 'linear-gradient(180deg, #2a1f1a 0%, #1a1a22 50%, #14141a 100%)',
    window: 'linear-gradient(180deg, #f59e0b 0%, #d97706 100%)',
    candle: 0.6,
  },
  noon: {
    bg: 'linear-gradient(180deg, #3a3025 0%, #2a2a30 50%, #1a1a22 100%)',
    window: 'linear-gradient(180deg, #fef3c7 0%, #fcd34d 100%)',
    candle: 0.2,
  },
  dusk: {
    bg: 'linear-gradient(180deg, #1f1a30 0%, #1a1a22 50%, #14141a 100%)',
    window: 'linear-gradient(180deg, #8b5cf6 0%, #c42b2b 100%)',
    candle: 0.8,
  },
  night: {
    bg: 'linear-gradient(180deg, #0a0a0d 0%, #050507 50%, #000 100%)',
    window: 'linear-gradient(180deg, #1e293b 0%, #0f172a 100%)',
    candle: 1.0,
  },
};

// 自动时辰
function autoTimeOfDay(hour: number): TimeOfDay {
  if (hour >= 5 && hour < 11) return 'dawn';
  if (hour >= 11 && hour < 17) return 'noon';
  if (hour >= 17 && hour < 21) return 'dusk';
  return 'night';
}

export const CourtBackdrop: React.FC<CourtBackdropProps> = ({
  timeOfDay,
  weather = 'clear',
  showCandles = true,
}) => {
  const [autoTime, setAutoTime] = useState<TimeOfDay>('dusk');

  useEffect(() => {
    if (timeOfDay) return;
    const update = () => setAutoTime(autoTimeOfDay(new Date().getHours()));
    update();
    const id = setInterval(update, 60_000);
    return () => clearInterval(id);
  }, [timeOfDay]);

  const time = timeOfDay ?? autoTime;
  const config = TIME_MAP[time];

  return (
    <div
      className={`court-backdrop court-backdrop-${time} court-backdrop-${weather}`}
      style={{ background: config.bg }}
    >
      {/* === 殿外远山 === */}
      <div className="court-backdrop-mountains" />

      {/* === 窗外光 === */}
      <div
        className="court-backdrop-window"
        style={{ background: config.window, opacity: 1 - config.candle }}
      />

      {/* === 殿柱 === */}
      <div className="court-backdrop-pillar court-backdrop-pillar-left" />
      <div className="court-backdrop-pillar court-backdrop-pillar-right" />

      {/* === 烛火粒子 === */}
      {showCandles && (
        <div
          className="court-backdrop-candles"
          style={{ opacity: config.candle }}
        >
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="court-backdrop-candle"
              style={{ left: `${10 + i * 18}%` }}
            >
              <div className="court-backdrop-flame" />
              <div className="court-backdrop-wick" />
              <div className="court-backdrop-candle-body" />
            </div>
          ))}
        </div>
      )}

      {/* === 天气粒子 === */}
      {weather === 'rain' && (
        <div className="court-backdrop-rain">
          {Array.from({ length: 50 }).map((_, i) => (
            <div
              key={i}
              className="court-backdrop-raindrop"
              style={{
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 2}s`,
                animationDuration: `${0.5 + Math.random() * 0.5}s`,
              }}
            />
          ))}
        </div>
      )}

      {weather === 'snow' && (
        <div className="court-backdrop-snow">
          {Array.from({ length: 30 }).map((_, i) => (
            <div
              key={i}
              className="court-backdrop-snowflake"
              style={{
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 5}s`,
                animationDuration: `${5 + Math.random() * 5}s`,
              }}
            >
              冬
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CourtBackdrop;
