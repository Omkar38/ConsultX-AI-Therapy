import { MessageCircleMore, Clock, Shield } from "lucide-react"
import { Link } from "@tanstack/react-router"
import type { ChatSession } from "@/types/session"

interface SessionHistoryProps {
  sessions: ChatSession[]
}

//  Session History Component
const SessionHistory = ( {sessions} : SessionHistoryProps ) => {
  const getSessionTypeIcon = () => { return <MessageCircleMore className="w-4 h-4" /> }
  const getSessionTypeColor = () => { return 'text-[#4A90A0]'}
  
  const getRiskColor = (tier: string) => {
    switch (tier) {
      case 'crisis': return 'text-red-600 bg-red-50'
      case 'high': return 'text-orange-600 bg-orange-50'
      case 'caution': return 'text-yellow-600 bg-yellow-50'
      case 'low': return 'text-blue-600 bg-blue-50'
      default: return 'text-green-600 bg-green-50'
    }
  }
  
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }
  
  return (
    <div className="bg-white rounded-xl shadow-sm p-6 h-full overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Recent Sessions</h3>
        <Link
        viewTransition
          to="/chat-new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#4A90A0] text-white rounded-lg text-sm font-medium hover:bg-[#70A8A2] transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          New Session
        </Link>
      </div>
      
      <div className="space-y-3">
        {sessions.length === 0 ? (
          <div className="text-center py-8">
            <MessageCircleMore className="w-8 h-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-500">No recent sessions</p>
          </div>
        ) : (
          sessions.map((session) => (
            <Link
              key={session.id}
              to="/feedback/$sessionId"
              params={{ sessionId: session.id }}
              className={`block ${session.status === 'ended' ? 'cursor-pointer' : 'cursor-default'}`}
            >
              <div className="flex items-start gap-3 p-3 rounded-lg bg-[#F6F4F2] hover:bg-[#E3E2F0] transition-colors">
                <div className={`p-2 rounded-lg bg-white ${getSessionTypeColor()}`}>
                  {getSessionTypeIcon()}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-gray-900">
                      Therapy Session
                    </p>
                    <span className="text-xs text-gray-500">
                      {formatDate(session.created_at)}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(session.active_risk_tier)}`}>
                      <Shield className="w-3 h-3" />
                      {session.active_risk_tier.toUpperCase()}
                    </span>
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                      session.status === 'active' ? 'text-green-600 bg-green-50' : 'text-gray-600 bg-gray-50'
                    }`}>
                      <div className={`w-2 h-2 rounded-full ${
                        session.status === 'active' ? 'bg-green-500' : 'bg-gray-400'
                      }`}></div>
                      {session.status}
                    </span>
                  </div>
                  
                  <p className="text-xs text-gray-500">
                    ID: {session.id.slice(0, 8)}...
                  </p>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}

export default SessionHistory;