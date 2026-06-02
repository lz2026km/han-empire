// SpeedControl 月/季/年速 (系统)
import React from 'react';
import './system.css';

export type Speed = 'month' | 'season' | 'year';

export interface SpeedControlProps {
  value: Speed;
  onChange: (v: Speed) => void;
}

const OPTIONS: Array<{ value: Speed; label: string; icon: string }> = [
  { value: 'month', label: '月', icon: '⏵' },
  { value: 'season', label: '季', icon: '下' },
  { value: 'year', label: '年', icon: '快' },
];

export const SpeedControl: React.FC<SpeedControlProps> = ({ value, onChange }) => {
  return (
    <div className="speed-control" role="group" aria-label="推进速度">
      {OPTIONS.map((o) => (
        <button type="button"
          key={o.value}
          className={`speed-btn ${value === o.value ? 'speed-btn-active' : ''}`}
          onClick={() => onChange(o.value)}
          aria-pressed={value === o.value}
        >
          {o.icon} {o.label}
        </button>
      ))}
    </div>
  );
};
export default SpeedControl;
