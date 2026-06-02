/* =============================================
   朝会布局组件 - Court Layout
   汉献帝之末路
   ============================================= */

import React, { useState, useCallback, useRef } from 'react';
import { MinisterPortrait } from './MinisterPortrait';

interface CourtMinister {
  id?: string;
  name: string;
  office: string;
  faction: string;
  status: 'active' | 'dismissed' | 'imprisoned' | 'exiled' | 'retired' | 'dead' | 'offstage';
  status_label: string;
  summary: string;
  portrait_id?: string;
  favorite?: boolean;
}

interface CourtLayoutProps {
  ministers: CourtMinister[];
  selectedMinister: string;
  onOpenChat: (minister: CourtMinister) => void;
  onUploadPortrait?: (ministerName: string, file: File) => Promise<void>;
  courtMode?: 'grid' | 'perspective';
}

const COURT_SLOTS_PER_ROW = 10;

const LEFT_ANCHOR = { near: { px: 0.08, py: 0.55 }, far: { px: 0.38, py: 0.08 } };
const RIGHT_ANCHOR = { near: { px: 0.92, py: 0.55 }, far: { px: 0.62, py: 0.08 } };

function courtSlots(): { px: number; py: number; side: 'left' | 'right'; slot: number }[] {
  const slots = [];
  for (let i = 0; i < COURT_SLOTS_PER_ROW; i++) {
    const t = i / (COURT_SLOTS_PER_ROW - 1);
    slots.push({
      px: LEFT_ANCHOR.near.px + t * (LEFT_ANCHOR.far.px - LEFT_ANCHOR.near.px),
      py: LEFT_ANCHOR.near.py + t * (LEFT_ANCHOR.far.py - LEFT_ANCHOR.near.py),
      side: 'left' as const,
      slot: i,
    });
    slots.push({
      px: RIGHT_ANCHOR.near.px + t * (RIGHT_ANCHOR.far.px - RIGHT_ANCHOR.near.px),
      py: RIGHT_ANCHOR.near.py + t * (RIGHT_ANCHOR.far.py - RIGHT_ANCHOR.near.py),
      side: 'right' as const,
      slot: i,
    });
  }
  return slots;
}

function snapToSlot(
  px: number,
  py: number,
  occupied: Set<string>,
  selfKey: string
): { px: number; py: number } {
  const slots = courtSlots();
  let best: { px: number; py: number } | null = null;
  let bestDist = Infinity;
  for (const s of slots) {
    const key = `${s.side}:${s.slot}`;
    if (occupied.has(key) && key !== selfKey) continue;
    const d = Math.hypot(s.px - px, s.py - py);
    if (d < bestDist) {
      bestDist = d;
      best = s;
    }
  }
  return best ?? { px, py };
}

function defaultCourtPct(index: number, total: number): { px: number; py: number } {
  const leftCount = Math.ceil(total / 2);
  const isLeft = index < leftCount;
  const posInRow = isLeft ? index : index - leftCount;
  const anchor = isLeft ? LEFT_ANCHOR : RIGHT_ANCHOR;
  const t = posInRow / (COURT_SLOTS_PER_ROW - 1);
  return {
    px: anchor.near.px + t * (anchor.far.px - anchor.near.px),
    py: anchor.near.py + t * (anchor.far.py - anchor.near.py),
  };
}

export function CourtLayout({
  ministers,
  selectedMinister,
  onOpenChat,
  onUploadPortrait,
  courtMode = 'grid',
}: CourtLayoutProps) {
  const [positions, setPositions] = useState<Record<string, { px: number; py: number }>>({});
  const [savedPosRef, setSavedPosRef] = useState<Record<string, { px: number; py: number }> | null>(null);
  const dragging = useRef<{
    name: string;
    startMX: number;
    startMY: number;
    startPX: number;
    startPY: number;
  } | null>(null);
  const didDrag = useRef(false);

  const listKey = ministers.map((m) => m.name).join('|');

  React.useEffect(() => {
    let cancelled = false;
    const allSlots = courtSlots();
    const next: Record<string, { px: number; py: number }> = {};
    const usedSlots = new Set<string>();

    ministers.forEach((m, index) => {
      const pct = defaultCourtPct(index, ministers.length);
      next[m.name] = pct;
    });

    if (!cancelled) {
      setPositions(next);
    }

    return () => {
      cancelled = true;
    };
  }, [listKey]);

  const onMouseDown = useCallback(
    (e: React.MouseEvent, name: string) => {
      if ((e.target as HTMLElement).closest('.portrait-upload-btn')) return;
      e.preventDefault();
      const pos = positions[name] || { px: 0.5, py: 0.8 };
      dragging.current = {
        name,
        startMX: e.clientX,
        startMY: e.clientY,
        startPX: pos.px,
        startPY: pos.py,
      };
      didDrag.current = false;

      const onMove = (ev: MouseEvent) => {
        if (!dragging.current) return;
        const dx = ev.clientX - dragging.current.startMX;
        const dy = ev.clientY - dragging.current.startMY;
        if (Math.abs(dx) > 3 || Math.abs(dy) > 3) didDrag.current = true;
        const el = document.getElementById('court-scene');
        if (!el) return;
        const { width, height } = el.getBoundingClientRect();
        const npx = Math.max(0, Math.min(1, dragging.current.startPX + dx / width));
        const npy = Math.max(0, Math.min(1, dragging.current.startPY + dy / height));
        setPositions((prev) => {
          const next = { ...prev, [dragging.current!.name]: { px: npx, py: npy } };
          return next;
        });
      };

      const onUp = () => {
        dragging.current = null;
        window.removeEventListener('mousemove', onMove);
        window.removeEventListener('mouseup', onUp);
      };

      window.addEventListener('mousemove', onMove);
      window.addEventListener('mouseup', onUp);
    },
    [positions]
  );

  if (courtMode === 'grid') {
    return (
      <div className="court-grid">
        {ministers.map((minister) => {
          const ousted = minister.status !== 'active';
          const dedicated = minister.portrait_id
            ? `/portraits/minister_${minister.id ?? minister.name}.png`
            : undefined;
          const poolFallback = minister.portrait_id
            ? `/portraits/${minister.portrait_id}.png`
            : undefined;

          return (
            <button
              key={minister.name}
              className={`minister-card ${selectedMinister === minister.name ? 'selected' : ''} ${
                ousted ? 'ousted' : ''
              }`}
              onClick={() => onOpenChat(minister)}
            >
              <div className="minister-card-portrait-wrap">
                <MinisterPortrait
                  primary={dedicated}
                  fallback={poolFallback}
                  name={minister.name}
                  size="medium"
                />
                {onUploadPortrait && (
                  <button
                    className="portrait-upload-btn"
                    title="上传立绘"
                    onClick={(e) => {
                      e.stopPropagation();
                    }}
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="17,8 12,3 7,8" />
                      <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                  </button>
                )}
              </div>
              <div className="minister-card-info">
                <div className="minister-card-top">
                  <span className="minister-name">{minister.name}</span>
                  {ousted && (
                    <span className={`minister-status status-${minister.status}`}>{minister.status_label}</span>
                  )}
                  {minister.office && <span className="minister-office">{minister.office}</span>}
                </div>
                <span className="minister-bio">{minister.summary}</span>
              </div>
              {minister.favorite && (
                <svg
                  className="favorite-mark"
                  width="13"
                  height="13"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <polygon points="12,2 15,9 22,9 17,14 19,21 12,17 5,21 7,14 2,9 9,9" />
                </svg>
              )}
            </button>
          );
        })}
      </div>
    );
  }

  return (
    <div id="court-scene" className="court-scene">
      <div className="emperor-throne">
        <div className="emperor-throne-icon">👑</div>
        <span className="emperor-throne-label">天子御座</span>
      </div>

      {ministers.map((minister, index) => {
        const ousted = minister.status !== 'active';
        const pct = positions[minister.name] || defaultCourtPct(index, ministers.length);
        const perspScale = 0.4 + 0.6 * pct.py;

        const dedicated = minister.portrait_id
          ? `/portraits/minister_${minister.id ?? minister.name}.png`
          : undefined;
        const poolFallback = minister.portrait_id ? `/portraits/${minister.portrait_id}.png` : undefined;

        return (
          <button
            key={minister.name}
            className={`court-minister-card ${selectedMinister === minister.name ? 'selected' : ''} ${
              ousted ? 'ousted' : ''
            }`}
            style={{
              left: `${pct.px * 100}%`,
              top: `${pct.py * 100}%`,
              cursor: 'grab',
              transform: `translate(-50%, -50%) scale(${perspScale.toFixed(3)})`,
              transformOrigin: 'bottom center',
              zIndex: Math.round(pct.py * 1000),
            }}
            onMouseDown={(e) => onMouseDown(e, minister.name)}
            onClick={(e) => {
              if (didDrag.current) {
                e.preventDefault();
                return;
              }
              onOpenChat(minister);
            }}
          >
            <div className="court-minister-portrait">
              <MinisterPortrait
                primary={dedicated}
                fallback={poolFallback}
                name={minister.name}
                size="large"
              />
            </div>
            <span className="court-minister-name">{minister.name}</span>
            {minister.office && <span className="court-minister-office">{minister.office}</span>}
            <span className={`court-minister-faction faction-badge-${minister.faction.toLowerCase()}`}>
              {minister.faction}
            </span>
          </button>
        );
      })}
    </div>
  );
}

export default CourtLayout;