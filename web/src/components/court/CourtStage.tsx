// ============================================
// 汉献帝之末路 v2.5.0 — 中央朝会剧场 CourtStage
// 殿堂背景 + 3-5 大臣立绘 + 主公中位 + 发言高亮
// ============================================

import React, { useState, useEffect } from 'react';
import { CourtBackdrop, TimeOfDay } from './CourtBackdrop';
import { MinistersPanel } from './MinistersPanel';
import { DebateBubble } from './DebateBubble';
import type { MinisterStats } from '../../types';
import './CourtStage.css';

export interface CourtStageProps {
  ministers?: MinisterStats[];
  topic?: string;
  weather?: 'clear' | 'rain' | 'snow';
  onMinisterSpeak?: (m: MinisterStats) => void;
}

export const CourtStage: React.FC<CourtStageProps> = ({
  ministers = [],
  topic = '诸卿平身, 今日朝会议事',
  weather = 'clear',
  onMinisterSpeak,
}) => {
  const [activeSpeaker, setActiveSpeaker] = useState<string | null>(null);

  // 演示数据
  const demoMinisters: MinisterStats[] = ministers.length > 0 ? ministers : [
    { id: 'caocao', name: '曹操', title: '兖州牧', faction: '主公', loyalty: 75, authority: 90, ability: 95, portrait: '操' },
    { id: 'yuanshao', name: '袁绍', title: '冀州牧', faction: '士族', loyalty: 30, authority: 95, ability: 80, portrait: '绍' },
    { id: 'sunjian', name: '孙坚', title: '豫州刺史', faction: '主公', loyalty: 80, authority: 70, ability: 88, portrait: '坚' },
    { id: 'liubiao', name: '刘表', title: '荆州牧', faction: '士族', loyalty: 50, authority: 85, ability: 75, portrait: '表' },
    { id: 'dongzhuo', name: '董卓', title: '太师', faction: '阉党', loyalty: 10, authority: 100, ability: 70, portrait: '卓' },
  ];

  // 自动时辰
  const [timeOfDay, setTimeOfDay] = useState<TimeOfDay>('dusk');
  useEffect(() => {
    const h = new Date().getHours();
    if (h >= 5 && h < 11) setTimeOfDay('dawn');
    else if (h >= 11 && h < 17) setTimeOfDay('noon');
    else if (h >= 17 && h < 21) setTimeOfDay('dusk');
    else setTimeOfDay('night');
  }, []);

  const handleMinisterClick = (m: MinisterStats) => {
    setActiveSpeaker(m.id);
    onMinisterSpeak?.(m);
    // 3s 后自动取消高亮
    setTimeout(() => setActiveSpeaker((cur) => (cur === m.id ? null : cur)), 3000);
  };

  return (
    <div className="court-stage">
      {/* === 背景层 === */}
      <CourtBackdrop timeOfDay={timeOfDay} weather={weather} />

      {/* === 朝会主题 === */}
      <div className="court-stage-topic">
        <div className="court-stage-topic-label imperial">朝议主题</div>
        <div className="court-stage-topic-text">{topic}</div>
      </div>

      {/* === 大臣立绘 === */}
      <MinistersPanel
        ministers={demoMinisters}
        activeSpeaker={activeSpeaker}
        onMinisterClick={handleMinisterClick}
      />

      {/* === 主公中位 (前景) === */}
      <div className="court-stage-emperor">
        <div className="court-stage-emperor-crown">冕</div>
        <div className="court-stage-emperor-body">帝</div>
        <div className="court-stage-emperor-name imperial">陛下</div>
      </div>

      {/* === 发言气泡 === */}
      {activeSpeaker && (() => {
        const speaker = demoMinisters.find((m) => m.id === activeSpeaker);
        if (!speaker) return null;
        const lines = [
          `${speaker.name}以为, 当...`,
          `臣${speaker.name} 谨奏: ...`,
          `${speaker.title} 不可不慎`,
        ];
        return (
          <DebateBubble
            speaker={speaker.name}
            line={lines[Math.floor(Math.random() * lines.length)]}
            stance={speaker.faction === '主公' ? 'support' : speaker.faction === '阉党' ? 'oppose' : 'neutral'}
          />
        );
      })()}
    </div>
  );
};

export default CourtStage;
