import React from 'react'
import { useTypewriter } from '@/hooks/useTypewriter'

interface TypewriterTextProps {
  text: string
  speed?: number
  startDelay?: number
  onComplete?: () => void
  className?: string
  showCursor?: boolean
}

export const TypewriterText: React.FC<TypewriterTextProps> = ({
  text,
  speed = 30,
  startDelay = 0,
  onComplete,
  className = '',
  showCursor = false
}) => {
  const { displayedText, isTyping, skipToEnd } = useTypewriter({
    text,
    speed,
    startDelay,
    onComplete
  })

  return (
    <span 
      className={className}
      onClick={isTyping ? skipToEnd : undefined}
      style={{ cursor: isTyping ? 'pointer' : 'default' }}
      title={isTyping ? 'Click to skip animation' : ''}
    >
      {displayedText}
      {showCursor && isTyping && (
        <span className="animate-pulse">|</span>
      )}
    </span>
  )
}

export default TypewriterText