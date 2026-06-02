// ============================================
// 汉献帝之末路 v3.2 — 新手引导
// 7 步浮层引导, 高亮 + 提示 + 强制等待
// ============================================

import React, { useEffect, useState } from 'react';

interface TutorialStep {
  id: string;
  order: number;
  title: string;
  description: string;
  target: string;
  position: 'top' | 'bottom' | 'left' | 'right';
  required_action: string | null;
  highlight_color: string;
  can_skip: boolean;
}

interface Progress {
  current_step: number;
  total_steps: number;
  completed_count: number;
  is_completed: boolean;
  skipped: boolean;
  percent: number;
}

export const Tutorial: React.FC<{ sessionId?: string; onComplete?: () => void }> = ({
  sessionId = 'default',
  onComplete,
}) => {
  const [progress, setProgress] = useState<Progress | null>(null);
  const [currentStep, setCurrentStep] = useState<TutorialStep | null>(null);
  const [allSteps, setAllSteps] = useState<TutorialStep[]>([]);
  const [loading, setLoading] = useState(true);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);

  const loadState = async () => {
    setLoading(true);
    try {
      const r = await fetch(`/api/tutorial?session_id=${sessionId}`);
      const d = await r.json();
      if (d.ok) {
        setProgress(d.progress);
        setCurrentStep(d.current_step);
        setAllSteps(d.all_steps);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadState(); }, [sessionId]);

  // 监听目标元素位置
  useEffect(() => {
    if (!currentStep || currentStep.target === '.app-header') {
      setTargetRect(null);
      return;
    }
    const updateRect = () => {
      const el = document.querySelector(currentStep.target);
      if (el) {
        setTargetRect(el.getBoundingClientRect());
      } else {
        setTargetRect(null);
      }
    };
    updateRect();
    window.addEventListener('resize', updateRect);
    window.addEventListener('scroll', updateRect, true);
    return () => {
      window.removeEventListener('resize', updateRect);
      window.removeEventListener('scroll', updateRect, true);
    };
  }, [currentStep]);

  if (loading || !progress || progress.is_completed) return null;

  const handleAdvance = async () => {
    const r = await fetch('/api/tutorial/advance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    });
    const d = await r.json();
    if (d.ok) {
      setProgress(d.progress);
      if (!d.has_next) {
        onComplete?.();
      } else {
        await loadState();
      }
    }
  };

  const handleSkip = async () => {
    const r = await fetch('/api/tutorial/skip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    });
    const d = await r.json();
    if (d.ok) {
      setProgress(d.progress);
      onComplete?.();
    }
  };

  if (!currentStep) return null;

  return (
    <>
      {/* 半透明遮罩 */}
      <div className="tutorial-overlay" onClick={currentStep.can_skip ? handleSkip : undefined} />

      {/* 高亮目标 */}
      {targetRect && (
        <div
          className="tutorial-highlight"
          style={{
            top: targetRect.top - 4,
            left: targetRect.left - 4,
            width: targetRect.width + 8,
            height: targetRect.height + 8,
            borderColor: currentStep.highlight_color,
            boxShadow: `0 0 0 9999px rgba(15, 23, 42, 0.7), 0 0 0 4px ${currentStep.highlight_color}`,
          }}
        />
      )}

      {/* 提示气泡 */}
      <div className={`tutorial-bubble position-${currentStep.position}`}
           style={targetRect ? {
             top: currentStep.position === 'bottom' ? targetRect.bottom + 12 :
                  currentStep.position === 'top' ? targetRect.top - 12 : targetRect.top,
             left: currentStep.position === 'left' ? targetRect.left - 12 :
                   currentStep.position === 'right' ? targetRect.right + 12 : targetRect.left,
           } : { top: '20%', left: '50%', transform: 'translateX(-50%)' }}>
        <div className="bubble-header">
          <span className="bubble-step">第 {currentStep.order + 1} / {progress.total_steps} 步</span>
          {currentStep.can_skip && (
            <button className="bubble-skip" onClick={handleSkip}>跳过</button>
          )}
        </div>
        <h3 className="bubble-title">{currentStep.title}</h3>
        <p className="bubble-desc">{currentStep.description}</p>
        {currentStep.required_action && (
          <div className="bubble-hint">请先完成动作: {currentStep.required_action}</div>
        )}
        <div className="bubble-footer">
          <div className="bubble-progress">
            <div className="bubble-bar" style={{ width: `${progress.percent}%`, background: currentStep.highlight_color }} />
          </div>
          <button className="bubble-next" onClick={handleAdvance}
                  style={{ background: currentStep.highlight_color }}>
            {currentStep.order >= progress.total_steps - 1 ? '完成' : '下一步'}
          </button>
        </div>
      </div>
    </>
  );
};

export default Tutorial;
