import React, { useEffect, useRef, useState, useCallback } from 'react'
import { useNavigate } from '@tanstack/react-router'

import SessionHeader from './components/SessionHeader'
import ControlButtons from './components/ControlButtons'
import AvatarDisplay from './components/AvatarDisplay'
import UserCameraView from './components/UserCameraView'
import { createChatSession, sendChatMessage, endChatSession } from '@/lib/api'
import type {
  ChatSession,
  ChatMessage,
  SendMessageResponse,
} from '@/types/session'

// Web Speech API types
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition
    webkitSpeechRecognition: typeof SpeechRecognition
  }
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  start(): void
  stop(): void
  abort(): void
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
  onend: (() => void) | null
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number
  results: SpeechRecognitionResultList
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string
}

interface SpeechRecognitionResultList {
  length: number
  item(index: number): SpeechRecognitionResult
  [index: number]: SpeechRecognitionResult
}

interface SpeechRecognitionResult {
  length: number
  item(index: number): SpeechRecognitionAlternative
  [index: number]: SpeechRecognitionAlternative
  isFinal: boolean
}

interface SpeechRecognitionAlternative {
  transcript: string
  confidence: number
}

declare var SpeechRecognition: {
  prototype: SpeechRecognition
  new (): SpeechRecognition
}

// Main video chat page component
function ChatLayout() {
  const [isMuted, setIsMuted] = useState(false)
  const [isCameraOff, setCameraOff] = useState(false)
  const [isConnected, setIsConnected] = useState(true)
  const [userId, setUserId] = useState<string | null>(null)

  // Chat state
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])  
  const [latestAssistantMessage, setLatestAssistantMessage] =
    useState<string>('')
  const [isChatVisible, setIsChatVisible] = useState(false)
  const [isLoading, setIsLoading] = useState(false)  // Speech recognition state
  const [isListening, setIsListening] = useState(false)
  const [speechRecognition, setSpeechRecognition] = useState<any>(null)

  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const navigate = useNavigate()

  // Initialize userId from localStorage on component mount
  useEffect(() => {
    const storedUserId = localStorage.getItem('userId')
    if (storedUserId) {
      console.log('ChatLayout: loaded userId from localStorage:', storedUserId)
      setUserId(storedUserId)
    } else {
      // Redirect to signup if no user ID found
      navigate({ to: '/signup' })
    }
  }, [])

  
   // Handle sending chat messages - use useCallback to prevent stale closures
  const handleSendMessage = useCallback(async (content: string) => {
    console.log("DEBUG: About to send message. CurrentSession:", currentSession?.id, "Content:", content)
    if (!currentSession) {
      console.log('DEBUG: No active session available when trying to send message')
      return
    } 

    setIsLoading(true)
    try {
      console.log('DEBUG: Sending message to session:', currentSession.id)
      const response = await sendChatMessage(currentSession.id, content)
      console.log('Message response:', response)

      // Add the user message
      if (response.message) {
        setMessages((prev) => [...prev, response.message])
      }
      
      // Add assistant message if it exists (it may not due to API issues)
      if (response.assistant_message) {
        setMessages((prev) =>
          response.assistant_message
            ? [...prev, response.assistant_message]
            : prev,
        )
        setLatestAssistantMessage(response.assistant_message.content)
      } else {
        // If no assistant message, show a fallback message
        const fallbackMessage: ChatMessage = {
          session_id: currentSession.id,
          sender: 'assistant',
          content:
            "I received your message. The AI response service is currently experiencing issues, but I'm here and listening.",
          sentiment_score: 0,
          risk_tier: 'ok',
          risk_score: 0,
          flagged_keywords: [],
          created_at: new Date().toISOString(),
          id: Date.now(), // Use timestamp as temp ID
        }
        setMessages((prev) => [...prev, fallbackMessage])
        setLatestAssistantMessage(fallbackMessage.content)
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      // Redirect to dashboard on error
      // navigate({ to: '/dashboard' })
    } finally {
      setIsLoading(false)
    }
  }, [currentSession]) // Add currentSession as dependency
  
  const handleEndSession = async () => {
    setIsConnected(false)

    // End the chat session if it exists
    if (currentSession) {
      try {
        await endChatSession(currentSession.id)
      } catch (error) {
        console.error('Failed to end session:', error)
        // Still continue with navigation even if API call fails
      }
    }

    // Stop camera stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    console.log('Session ended')

    // Navigate to feedback page
    setTimeout(() => {
      if (currentSession) {
        navigate({ to: '/feedback/$sessionId', params: { sessionId: currentSession.id } })
      } else {
        navigate({ to: '/dashboard' })
      }
    }, 1000)
  }

  const toggleCamera = () => setCameraOff(!isCameraOff)

  // Initialize speech recognition - reinitialize when currentSession changes to fix stale closure
  useEffect(() => {
    console.log('DEBUG: Initializing speech recognition. CurrentSession:', currentSession?.id)
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      const recognition = new SpeechRecognition()
      
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'en-US'
      
      recognition.onresult = (event: any) => {
        let finalTranscript = ''
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            finalTranscript += transcript
          }
        }
        
        if (finalTranscript.trim()) {
          console.log('DEBUG: Speech recognition final transcript:', finalTranscript.trim())
          console.log('DEBUG: Current session at speech recognition time:', currentSession?.id)
          handleSendMessage(finalTranscript.trim()) 
        }
      }
      
      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error)
        setIsListening(false)
      }
      
      recognition.onend = () => {
        setIsListening(false)
      }
      
      setSpeechRecognition(recognition)
    }
  }, [handleSendMessage, currentSession]) // Add dependencies to reinitialize when they change

  // Toggle speech recognition
  const toggleSpeechRecognition = () => {
    if (!speechRecognition) {
      alert('Speech recognition is not supported in this browser')
      return
    }
    console.log('Toggling speech recognition. Currently listening:', isListening)
    if (isListening) {
      speechRecognition.stop()
      setIsListening(false)
    } else {
      speechRecognition.start()
      setIsListening(true)
    }
  }

  // Create session when component mounts and userId is available
  useEffect(() => {
    const initializeSession = async () => {
      if (!userId) {
        // Don't try to create session if userId is not loaded yet
        console.log('DEBUG: No userId yet, waiting...')
        return
      }

      try {
        console.log('DEBUG: Creating session for userId:', userId)
        const session = await createChatSession(userId)
        console.log('DEBUG: Created new chat session:', session)
        setCurrentSession(session)
      } catch (error) {
        console.error('Failed to create session:', error)
        navigate({ to: '/dashboard' })
      }
    }

    initializeSession()
  }, [userId, navigate])

  // Debug currentSession changes
  useEffect(() => {
    console.log('DEBUG: currentSession changed to:', currentSession)
  }, [currentSession])

  // Camera management
  useEffect(() => {
    let mounted = true

    const startCamera = async () => {
      if (isCameraOff || !isConnected) {
        // Stop existing stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop())
          streamRef.current = null
        }
        return
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 320, height: 240 },
          audio: true, // Enable audio for speech recognition
        })

        if (!mounted) {
          stream.getTracks().forEach((track) => track.stop())
          return
        }

        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          videoRef.current.play().catch(() => {})
        }
      } catch (error) {
        console.log('Unable to access camera:', error)
      }
    }

    startCamera()

    return () => {
      mounted = false
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
        streamRef.current = null
      }
    }
  }, [isCameraOff, isConnected])

  return (
    <div className="h-screen w-screen bg-linear-to-br from-[#D8EFE8] to-[#E3E2F0] overflow-hidden">
      {/* Session Header */}
      <SessionHeader isConnected={isConnected} />

      {/* Main Avatar Area */}
      <div className="h-full w-full relative flex">
        <AvatarDisplay
          latestMessage={latestAssistantMessage}
          onToggleChat={() => setIsChatVisible(!isChatVisible)}
          isChatVisible={isChatVisible}
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          isListening={isListening}
          // onToggleSpeechRecognition={toggleSpeechRecognition}
        />

        {/* User Camera View - Floating */}
        {isConnected && (
          <UserCameraView isCameraOff={isCameraOff} videoRef={videoRef} />
        )}

        {/* Control Buttons */}
        {isConnected && (
          <ControlButtons
            // isMuted={isMuted}
            isCameraOff={isCameraOff}
            // onToggleMute={toggleMute}
            onToggleCamera={toggleCamera}
            onEndSession={handleEndSession}
            isListening={isListening}
            onToggleSpeechRecognition={toggleSpeechRecognition}
          />
        )}
      </div>
    </div>
  )
}

export default ChatLayout
