// ============================================
// 汉献帝之末路 v2.5.0 — AppLayout 三栏骨架
// 1920×1080 锁死 / 1280×720 兜底 / 零滚动
// ============================================

import React, { ReactNode } from 'react';
import { TopBar } from './components/topbar/TopBar';
import { EventTicker } from './components/events/EventTicker';
import type { GameState } from './types';
import './AppLayout.css';

export interface AppLayoutProps {
  gameState: GameState | null;
  inbox: ReactNode;           // 左 280
  court: ReactNode;           // 中 880
  dashboard: ReactNode;       // 右 360
  topbarExtra?: ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  gameState,
  inbox,
  court,
  dashboard,
  topbarExtra,
}) => {
  return (
    <div className="app-layout">
      {/* === 顶部状态栏 64px === */}
      <header className="app-topbar">
        <TopBar gameState={gameState} extra={topbarExtra} />
      </header>

      {/* === 主体三栏 === */}
      <main className="app-main">
        <aside className="app-left">{inbox}</aside>
        <section className="app-center">{court}</section>
        <aside className="app-right">{dashboard}</aside>
      </main>

      {/* === 底部事件流 48px === */}
      <footer className="app-bottom">
        <EventTicker />
      </footer>
    </div>
  );
};

export default AppLayout;
