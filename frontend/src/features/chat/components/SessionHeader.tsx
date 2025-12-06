import React, { useEffect, useState } from 'react'

// Session header component
interface SessionHeaderProps {
  isConnected: boolean
}

const SessionHeader = ({ isConnected }: SessionHeaderProps) => {
  const [sessionTime, setSessionTime] = useState(0)

  useEffect(() => {
    if (!isConnected) return

    const interval = setInterval(() => {
      setSessionTime((prev) => prev + 1)
    }, 1000)

    return () => clearInterval(interval)
  }, [isConnected])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="absolute top-6 left-6 right-6 flex items-center justify-between z-10">
      <div className="bg-white/90 backdrop-blur-sm rounded-xl px-4 py-2 shadow-sm">
        <h1 className="text-lg font-medium text-gray-900">Wellness Session</h1>
        <p className="text-sm text-gray-600">
          {isConnected ? 'Connected' : 'Session ended'}
        </p>
      </div>
      
      <div className="bg-white/90 backdrop-blur-sm rounded-xl px-4 py-2 shadow-sm flex items-center gap-2">
        <div
          className={`w-2 h-2 rounded-full ${
            isConnected ? 'bg-[#6BAF7A]' : 'bg-gray-400'
          }`}
        />
        <span className="text-sm font-medium text-gray-700">
          {isConnected ? formatTime(sessionTime) : 'Disconnected'}
        </span>
      </div>
    </div>
  )
}

export default SessionHeader