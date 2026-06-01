// ============================================
// 汉献帝之末路 v2.5.0 — 全局快捷键 useKeyboard
// J/K 切换奏折 / Esc 关闭弹窗 / 1-5 切档 / Space 推进
// ============================================

import { useEffect, useCallback, useRef } from 'react';

export interface KeyBindings {
  // 奏折切换
  j?: () => void;        // 下一封
  k?: () => void;        // 上一封
  // 弹窗
  Escape?: () => void;
  // 拟旨
  '1'?: () => void;      // 口谕
  '2'?: () => void;
  '3'?: () => void;
  '4'?: () => void;
  '5'?: () => void;
  // 推进
  ' ': () => void;
  // 菜单
  m?: () => void;        // 菜单
  s?: () => void;        // 设置
  h?: () => void;        // 起居注
  // 任意自定义
  [key: string]: (() => void) | undefined;
}

export function useKeyboard(bindings: KeyBindings, enabled = true) {
  const bindingsRef = useRef(bindings);
  bindingsRef.current = bindings;

  const handler = useCallback(
    (e: KeyboardEvent) => {
      if (!enabled) return;

      // 输入框内不触发
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      const key = e.key === ' ' ? ' ' : e.key;
      const handler = bindingsRef.current[key];
      if (handler) {
        e.preventDefault();
        handler();
      }
    },
    [enabled]
  );

  useEffect(() => {
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handler]);
}

export default useKeyboard;
