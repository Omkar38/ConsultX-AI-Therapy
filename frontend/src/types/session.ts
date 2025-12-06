interface Session {
  id: string
  date: string
  duration: number
  notes: string
  type: 'therapy' | 'check-in' | 'emergency'
}

// Chat session types
export interface ChatSession {
  id: string
  user_id: string
  status: 'active' | 'ended'
  created_at: string
  updated_at: string
  active_risk_tier: 'ok' | 'low' | 'caution' | 'high' | 'crisis'
  metadata: Record<string, any>
}

export interface CreateSessionResponse {
  session: ChatSession
  buffer: MessageBuffer
}

export interface ChatMessage {
  session_id: string
  sender: 'user' | 'assistant'
  content: string
  sentiment_score: number
  risk_tier: 'ok' | 'low' | 'caution' | 'high' | 'crisis'
  risk_score: number
  flagged_keywords: string[]
  created_at: string
  id: number
}

export interface RiskAssessment {
  tier: 'ok' | 'low' | 'caution' | 'high' | 'crisis'
  score: number
  flagged_keywords: string[]
  notes: string[]
}

export interface MessageBuffer {
  session_id: string
  capacity: number
  messages: ChatMessage[]
}

export interface SendMessageResponse {
  message: ChatMessage
  risk: RiskAssessment
  buffer: MessageBuffer
  metrics: {
    session_id: string
    message_count: number
    user_turns: number
    assistant_turns: number
    avg_sentiment: number
    max_risk_tier: string
    tier_counts: Record<string, number>
    band_counts: Record<string, number>
    trend_notes: string[]
    suggested_resources: string[]
  }
  assistant_message?: ChatMessage // Optional since it may not be present
}

export interface SessionSummary {
  summary: {
    session: {
      id: string
      user_id: string
      status: string
      created_at: string
      updated_at: string
      active_risk_tier: string
      metadata: Record<string, any>
    }
    metrics: {
      session_id: string
      message_count: number
      user_turns: number
      assistant_turns: number
      avg_sentiment: number
      max_risk_tier: string
      tier_counts: {
        ok: number
        caution: number
        high: number
        crisis: number
      }
      band_counts: {
        positive: number
        neutral: number
        negative: number
      }
      trend_notes: string[]
      suggested_resources: Array<{
        type: string
        label: string
        link?: string
      }>
    }
    duration_seconds: number
    flagged_keywords: string[]
    notes: string[]
  }
}