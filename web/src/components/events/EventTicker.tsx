// ============================================
// 汉献帝之末路 v2.5.0 — 底部事件流 EventTicker
// 5-7 行横向滚动 / 时间锚定
// ============================================

import React from 'react';
import './EventTicker.css';

export interface EventTickerProps {
  events?: Array<{ time: string; text: string; important?: boolean }>;
}

const DEFAULT_EVENTS: EventTickerProps['events'] = [
  { time: '本月', text: '冀州大旱, 颗粒无收', important: true },
  { time: '本月', text: '曹操献马三千以充军资' },
  { time: '上月', text: '袁绍表奏请增兵冀州' },
  { time: '上月', text: '孙坚斩华雄, 声名大振' },
  { time: '两月前', text: '刘备受诏领豫州牧' },
];

export const EventTicker: React.FC<EventTickerProps> = ({
  events = DEFAULT_EVENTS,
}) => {
  return (
    <div className="event-ticker">
      <div className="event-ticker-label">事件流</div>
      <div className="event-ticker-track">
        {events.map((e, i) => (
          <div
            key={i}
            className={`event-ticker-item ${e.important ? 'event-ticker-important' : ''}`}
          >
            <span className="event-ticker-time">{e.time}</span>
            <span className="event-ticker-text">{e.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EventTicker;
