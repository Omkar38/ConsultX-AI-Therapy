import React, { useEffect, useState, useRef } from 'react'
import { AudioLines, MessageCircleMore, MessageCircle, Send, Mic, MicOff } from 'lucide-react'
import type { ChatMessage } from '@/types/session'
import TypewriterText from '@/components/TypewriterText'

interface AvatarDisplayProps {
  latestMessage: string
  onToggleChat: () => void
  isChatVisible: boolean
  messages: ChatMessage[]
  onSendMessage: (content: string) => void
  isLoading: boolean
  isListening: boolean
  // onToggleSpeechRecognition: () => void
}

const AvatarDisplay: React.FC<AvatarDisplayProps> = ({ 
  latestMessage, 
  onToggleChat, 
  isChatVisible, 
  messages, 
  onSendMessage, 
  isLoading,
  isListening,
  // onToggleSpeechRecognition
}) => {

  const [isSpeaking, setIsSpeaking] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

//   // Simulate conversation states (need to tweak with real data later)
//   useEffect(() => {
//     const interval = setInterval(() => {
//       setIsListening((prev) => !prev)
//       setTimeout(() => {
//         setIsSpeaking((prev) => !prev)
//       }, 2000)
//     }, 8000)

//     return () => clearInterval(interval)
//   }, [])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = () => {
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue.trim())
      setInputValue('')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 relative">
      {/* Avatar Circle */}
      <div className="relative mb-8">
        <div
          className={`w-48 h-48 rounded-full flex items-center justify-center transition-all duration-1000 ${
            isListening
              ? 'bg-linear-to-br from-[#70A8A2] to-[#4A90A0] scale-105'
              : isSpeaking
                ? 'bg-linear-to-br from-[#6879A1] to-[#4A90A0] scale-110'
                : 'bg-linear-to-br from-[#4A90A0] to-[#6879A1]'
          }`}
        >
          {isListening ? <AudioLines size={100} strokeWidth={1.5} color="#ffffff"/> : <MessageCircleMore size={100} strokeWidth={1.5} color="#ffffff" />}
        </div>
        
        {/* Listening/Speaking indicator rings */}
        {(isListening || isSpeaking) && (
          <div className="absolute inset-0 rounded-full">
            <div
              className={`absolute inset-0 rounded-full border-2 animate-ping ${
                isListening ? 'border-[#70A8A2]' : 'border-[#6879A1]'
              }`}
              style={{ animationDuration: '2s' }}
            />
          </div>
        )}
      </div>

      {/* Status Text / Latest Message */}
      <div className="text-center max-w-md mb-4">
        <h2 className="text-xl font-medium text-gray-800 mb-2">
          {isListening
            ? 'Listening to your voice...'
            : isSpeaking
              ? 'Speaking...'
              : 'Ready to help'}
        </h2>
        {latestMessage ? (
          <div className="bg-white/80 p-4 rounded-lg shadow-md">
            <TypewriterText 
              text={latestMessage}
              speed={25}
              className="text-sm text-gray-700 leading-relaxed"
              showCursor={true}
            />
          </div>
        ) : (
          <p className="text-base text-gray-600 leading-relaxed">
            {isListening
              ? 'Speak naturally - I\'ll send your message when you finish talking.'
              : isSpeaking
                ? 'Let me share some thoughts on what you\'ve said.'
                : 'Your wellness companion is ready when you are. Use voice or text to communicate.'}
          </p>
        )}
      </div>

      {/* Control Buttons */}
      <div className="flex items-center gap-3 mb-4">
  
        {/* Chat Toggle Button */}
        <button
          onClick={onToggleChat}
          className="flex items-center gap-2 px-4 py-2 bg-white/90 hover:bg-white text-gray-700 rounded-full shadow-lg transition-colors"
        >
          <MessageCircle size={20} />
          {isChatVisible ? 'Hide Chat' : 'Open Chat'}
        </button>
      </div>

      {/* Chat Interface */}
      {isChatVisible && (
        <div className="absolute right-4 top-4 bottom-4 w-80 bg-white rounded-lg shadow-xl flex flex-col">
          {/* Chat Header */}
          <div className="p-4 border-b">
            <h3 className="font-medium text-gray-800">Therapy Chat</h3>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 text-sm">
                Start the conversation by sending a message.
              </div>
            )}
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] px-3 py-2 rounded-lg text-sm ${
                    message.sender === 'user'
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-gray-100 text-gray-900 rounded-bl-none'
                  }`}
                >
                  {message.content}
                  <div className="text-[10px] opacity-60 text-right mt-1">
                    {new Date(message.created_at).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-3 py-2 rounded-lg text-sm text-gray-600">
                  Typing...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t">
            <div className="flex gap-2">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Type your message..."
                className="flex-1 rounded-md border px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
                rows={2}
                disabled={isLoading}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="inline-flex items-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AvatarDisplay