// ============================================
// 汉献帝之末路 v3.2 — PC 大屏沉浸模式
// 1920×1080 锁死, 隐藏状态栏, 黑边压暗, F11 切换
// ============================================

import React, { useEffect, useState } from 'react';

interface Props {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
}

export const ImmersiveMode: React.FC<Props> = ({ enabled, onToggle }) => {
  const [mouseIdle, setMouseIdle] = useState(false);

  // F11 / Esc 切换
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'F11') {
        e.preventDefault();
        onToggle(!enabled);
      } else if (e.key === 'Escape' && enabled) {
        onToggle(false);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [enabled, onToggle]);

  // 鼠标空闲检测
  useEffect(() => {
    if (!enabled) return;
    let timer: number;
    const reset = () => {
      setMouseIdle(false);
      clearTimeout(timer);
      timer = window.setTimeout(() => setMouseIdle(true), 5000);
    };
    window.addEventListener('mousemove', reset);
    reset();
    return () => {
      window.removeEventListener('mousemove', reset);
      clearTimeout(timer);
    };
  }, [enabled]);

  // 沉浸模式: 隐藏状态栏
  useEffect(() => {
    document.body.classList.toggle('immersive-mode', enabled);
    return () => { document.body.classList.remove('immersive-mode'); };
  }, [enabled]);

  if (!enabled) return null;

  return (
    <>
      <div className={`immersive-cursor ${mouseIdle ? 'idle' : 'active'}`} />
      <div className="immersive-hint">
        按 <kbd>Esc</kbd> 退出沉浸模式 · <kbd>F11</kbd> 切换
      </div>
    </>
  );
};

export default ImmersiveMode;
