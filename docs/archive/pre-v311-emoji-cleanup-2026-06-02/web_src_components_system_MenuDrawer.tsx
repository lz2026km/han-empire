// MenuDrawer 右滑菜单 (系统)
import React from 'react';
import './system.css';

export interface MenuDrawerProps {
  open: boolean;
  onClose: () => void;
}

const ITEMS = [
  { icon: '💾', label: '存档' },
  { icon: '📂', label: '读档' },
  { icon: '📜', label: '起居注' },
  { icon: '⚙', label: '设置' },
  { icon: '🚪', label: '退出' },
];

export const MenuDrawer: React.FC<MenuDrawerProps> = ({ open, onClose }) => {
  if (!open) return null;
  return (
    <>
      <div className="system-overlay" onClick={onClose} />
      <div className="menu-drawer">
        <div className="menu-drawer-header">
          <h3 className="imperial">菜单</h3>
          <button onClick={onClose} aria-label="关闭">×</button>
        </div>
        {ITEMS.map((it) => (
          <button key={it.label} className="menu-drawer-item">
            <span className="menu-drawer-icon">{it.icon}</span>
            <span>{it.label}</span>
          </button>
        ))}
      </div>
    </>
  );
};
export default MenuDrawer;
