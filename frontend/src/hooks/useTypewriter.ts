import { useState, useEffect, useRef } from 'react'

interface UseTypewriterOptions {
  text: string
  speed?: number
  startDelay?: number
  onComplete?: () => void
}

export function useTypewriter({ 
  text, 
  speed = 30, 
  startDelay = 0, 
  onComplete 
}: UseTypewriterOptions) {
  const [displayedText, setDisplayedText] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const indexRef = useRef(0)

  useEffect(() => {
    // Reset when text changes
    setDisplayedText('')
    setIsTyping(true)
    indexRef.current = 0

    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    // Start typing after delay
    timeoutRef.current = setTimeout(() => {
      typeText()
    }, startDelay)

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [text])

  const typeText = () => {
    if (indexRef.current < text.length) {
      setDisplayedText(text.slice(0, indexRef.current + 1))
      indexRef.current++
      
      timeoutRef.current = setTimeout(() => {
        typeText()
      }, speed)
    } else {
      setIsTyping(false)
      onComplete?.()
    }
  }

  const skipToEnd = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setDisplayedText(text)
    setIsTyping(false)
    indexRef.current = text.length
    onComplete?.()
  }

  return {
    displayedText,
    isTyping,
    skipToEnd
  }
}