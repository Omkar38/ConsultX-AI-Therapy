import React, { useEffect, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

// Types
type Message = {
  id: string
  role: 'user' | 'ai'
  text: string
  timestamp: number
}

// Helper to simulate a mock AI response
const mockAIGenerate = async (userMessage: string) => {
  // Simulate network latency and processing
  await new Promise((res) => setTimeout(res, 1000 + Math.random() * 1000))
  // Return a canned response that references the user's message
  return `I hear you. You said: "${userMessage}" — let's explore that further.`
}

// Subcomponent: Message bubble
function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} py-1`}
      aria-live={isUser ? 'polite' : undefined}
    >
      <div
        className={`max-w-[80%] px-3 py-2 rounded-lg text-sm break-words whitespace-pre-wrap shadow-sm ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-none'
            : 'bg-gray-100 text-gray-900 rounded-bl-none'
        }`}
      >
        {message.text}
        <div className="text-[10px] opacity-60 text-right mt-1">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}

// Subcomponent: Message list
function MessageList({ messages }: { messages: Message[] }) {
  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    // Auto-scroll to bottom when messages change
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="overflow-auto p-4 space-y-2" role="log" aria-live="polite">
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}

// Subcomponent: Chat input form
function ChatInput({
  onSend,
  disabled,
}: {
  onSend: (text: string) => void
  disabled?: boolean
}) {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  const submit = (e?: React.FormEvent) => {
    e?.preventDefault()
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
    textareaRef.current?.focus()
  }

  return (
    <form
      className="p-3 border-t bg-white"
      onSubmit={submit}
      aria-label="Send a message"
    >
      <div className="flex gap-2">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e: React.KeyboardEvent<HTMLTextAreaElement>) => {
            // Pressing Enter (without Shift) will submit the message
            if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
            }
          }}
          rows={2}
          className="flex-1 rounded-md border px-2 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
          placeholder="Type your message..."
          aria-label="Message text"
        />
        <div className="flex flex-row gap-1">
            <button
            type="submit"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            disabled={!text.trim() || disabled}
            aria-disabled={!text.trim() || disabled}
            >
            Send
            </button>
            <button className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50">Mic</button>
        </div>
      </div>
    </form>
  )
}

export default function TherapyChatInterface() {
  const [messages, setMessages] = useState<Message[]>(() => [
    {
      id: 'ai-1',
      role: 'ai',
      text: "Hello — I'm here to listen. What's on your mind today?",
      timestamp: Date.now(),
    },
  ])

  // Camera state
  const [cameraOn, setCameraOn] = useState(true)
  const [cameraError, setCameraError] = useState<string | null>(null)
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  // Mutation for sending user message and receiving AI response
  const mutation = useMutation<string, unknown, string, unknown>({
    mutationFn: async (userText: string) => {
      const aiText = await mockAIGenerate(userText)
      return aiText
    },
  })
  const [isGenerating, setIsGenerating] = useState(false)

  // Handle send
  const handleSend = (text: string) => {
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      text,
      timestamp: Date.now(),
    }

    setMessages((m) => [...m, userMessage])

    setIsGenerating(true)
    mutation.mutate(text, {
      onSuccess: (aiText: string) => {
        const aiMessage: Message = {
          id: `ai-${Date.now()}`,
          role: 'ai',
          text: aiText,
          timestamp: Date.now(),
        }
        setMessages((prev) => [...prev, aiMessage])
        setIsGenerating(false)
      },
      onError: () => {
        const errMsg: Message = {
          id: `ai-err-${Date.now()}`,
          role: 'ai',
          text: 'Sorry, something went wrong while generating a response.',
          timestamp: Date.now(),
        }
        setMessages((prev) => [...prev, errMsg])
        setIsGenerating(false)
      },
    })
  }

  // Start camera
  useEffect(() => {
    let mounted = true

    const startCamera = async () => {
      if (!cameraOn) return
      try {
        const s = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        })
        if (!mounted) return
        streamRef.current = s
        if (videoRef.current) {
          videoRef.current.srcObject = s
          videoRef.current.play().catch(() => {})
        }
        setCameraError(null)
      } catch (e: any) {
        setCameraError(e?.message || 'Unable to access the camera.')
      }
    }

    startCamera()

    return () => {
      mounted = false
      // Stop tracks
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop())
        streamRef.current = null
      }
    }
  }, [cameraOn])

  // Toggle camera
  const toggleCamera = () => setCameraOn((v) => !v)

  return (
    <div className="h-screen w-screen grid grid-cols-10">
      {/* Left side: 7/10 */}
      <div className="h-full col-span-7 relative bg-black flex items-center justify-center overflow-hidden">
        {cameraOn && !cameraError ? (
          <video
            ref={videoRef}
            className="w-full h-full object-cover"
            playsInline
            muted
            aria-label="Live webcam feed"
          />
        ) : (
          <div className="text-center text-white p-4">
            <p className="font-semibold">Camera unavailable</p>
            <p className="text-sm opacity-80 mt-2">
              {cameraError ?? 'Camera is turned off.'}
            </p>
          </div>
        )}

        <button
          onClick={toggleCamera}
          className="absolute top-4 right-4 z-20 inline-flex items-center gap-2 bg-white/80 text-black px-3 py-2 rounded-md shadow hover:bg-white"
          aria-pressed={!cameraOn}
        >
          {cameraOn ? 'Turn camera off' : 'Turn camera on'}
        </button>
      </div>

      {/* Right side: 3/10 */}
      <div className="col-span-3 flex flex-col border-l bg-white min-h-0">
        <header className="p-3 border-b">
          <h2 className="text-lg font-semibold">Therapy Chat</h2>
        </header>

        <div className="flex-1 min-h-0 overflow-y-scroll">
          <MessageList messages={messages} />
        </div>

        <div>
          <ChatInput onSend={handleSend} disabled={isGenerating} />
          {isGenerating && (
            <div className="p-2 text-center text-sm text-gray-600">
              AI is typing...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
