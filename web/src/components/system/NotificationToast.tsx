// NotificationToast 飞入通知 (系统)
import React, { useEffect, useState } from 'react';
import './system.css';

export type ToastType = 'success' | 'warning' | 'error' | 'info';

export interface NotificationToastProps {
  message: string;
  type?: ToastType;
  duration?: number;
  onClose?: () => void;
}

export const NotificationToast: React.FC<NotificationToastProps> = ({
  message, type = 'info', duration = 3000, onClose,
}) => {
  useEffect(() => {
    if (!duration) return;
    const id = setTimeout(() => onClose?.(), duration);
    return () => clearTimeout(id);
  }, [duration, onClose]);

  return (
    <div className={`notif-toast notif-toast-${type}`} role="status">
      <span className={`notif-icon notif-icon--${type === 'error' ? 'critical' : type}`} aria-hidden="true" />
      <span className="notif-toast-msg">{message}</span>
    </div>
  );
};

// 简易队列管理
export function useToasts() {
  const [toasts, setToasts] = useState<Array<{ id: number; message: string; type: ToastType }>>([]);
  const push = (message: string, type: ToastType = 'info') => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, message, type }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3000);
  };
  return { toasts, push };
}
export default NotificationToast;
