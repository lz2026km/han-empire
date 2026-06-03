import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import './SceneTransition.css'

type TransitionType = 'fade' | 'wipe-left' | 'wipe-right' | 'curtain-up' | 'curtain-down' | 'slide-left' | 'slide-right'

interface SceneTransitionProps {
  children: ReactNode
  isActive?: boolean
  type?: TransitionType
  duration?: number
}

export function SceneTransition({
  children,
  isActive = true,
  type = 'fade',
  duration = 400
}: SceneTransitionProps) {
  const [animating, setAnimating] = useState(false)

  useEffect(() => {
    if (isActive) {
      setAnimating(true)
      const timer = setTimeout(() => setAnimating(false), duration)
      return () => clearTimeout(timer)
    }
  }, [isActive, duration])

  if (!isActive && !animating) {
    return <>{children}</>
  }

  return (
    <div 
      className={`scene-transition scene-transition--${type}`}
      style={{ '--transition-duration': `${duration}ms` } as React.CSSProperties}
    >
      <div className="scene-transition__curtain" />
      <div className="scene-transition__content">
        {children}
      </div>
    </div>
  )
}