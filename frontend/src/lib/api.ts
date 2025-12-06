import type { MoodEntry } from '@/types/dashboard'
import type { ChatSession, SendMessageResponse, SessionSummary, CreateSessionResponse } from '@/types/session'

const API_BASE_URL = 'http://localhost:8000'

// User data from backend
export interface User {
  id: string
  name: string
  email: string
  joined_date: string
}

// Weather data from backend
export interface Weather {
  temperature: number
  description: string
  humidity: number
  location: string
}

// Session data from backend
export interface Session {
  id: string
  date: string
  duration: number
  notes: string
  type: 'therapy' | 'check-in' | 'emergency'
}

// API response wrappers
export interface UserResponse {
  user: User
}

export interface WeatherResponse {
  weather: Weather
}

export interface MoodEntriesResponse {
  mood_entries: MoodEntry[]
  user_id: string
}

export interface ChatSessionsResponse {
  sessions: ChatSession[]
}

/**
 * Fetch user profile data
 */
export async function fetchUser(userId: string): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/user/${userId}`)
  
  if (!response.ok) {
    throw new Error(`Failed to fetch user: ${response.statusText}`)
  }
  
  const data: UserResponse = await response.json()
  return data.user
}

/**
 * Fetch current weather data
 */
export async function fetchWeather(): Promise<Weather> {
  const response = await fetch(`${API_BASE_URL}/weather`)
  
  if (!response.ok) {
    throw new Error(`Failed to fetch weather: ${response.statusText}`)
  }
  
  const data: WeatherResponse = await response.json()
  return data.weather
}

/**
 * Fetch mood entries for a user
 */
export async function fetchMoodEntries(userId: string): Promise<MoodEntry[]> {
  const response = await fetch(`${API_BASE_URL}/mood-entries?user_id=${userId}`)
  
  if (!response.ok) {
    throw new Error(`Failed to fetch mood entries: ${response.statusText}`)
  }
  
  const data: MoodEntriesResponse = await response.json()
  return data.mood_entries
}

/**
 * Fetch sessions for a user
 */
export async function fetchSessions(userId: string): Promise<ChatSession[]> {
  const response = await fetch(`${API_BASE_URL}/sessions?user_id=${userId}`)
  
  if (!response.ok) {
    throw new Error(`Failed to fetch sessions: ${response.statusText}`)
  }
  
  const data: ChatSessionsResponse = await response.json()
  return data.sessions
}

/**
 * Add a new mood entry for a user
 */
export async function addMoodEntry(userId: string, date: string, mood: number): Promise<MoodEntry> {
  console.log('Adding mood entry:', { userId, date, mood })
  const response = await fetch(`${API_BASE_URL}/mood-entries`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId, date, mood }),
  })

  if (!response.ok) {
    throw new Error(`Failed to add mood entry: ${response.statusText}`)
  }

  const data = await response.json()
  return { date: data.entry.date, mood: data.entry.mood }
}

/**
 * Signup a new user
 */
export async function signupUser({ name, password }: { name: string; password: string }) {
  const response = await fetch(`${API_BASE_URL}/signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name, password }),
  })
  if (!response.ok) {
    throw new Error('Signup failed: ' + response.statusText)
  }
  return await response.json()
}

/**
 * Login a user
 */
export async function loginUser({ name, password }: { name: string; password: string }) {
  const response = await fetch(`${API_BASE_URL}/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name, password }),
  })
  if (!response.ok) {
    throw new Error('Login failed: ' + response.statusText)
  }
  return await response.json()
}

/**
 * Create a new chat session
 */
export async function createChatSession(userId: string): Promise<ChatSession> {
  const response = await fetch(`${API_BASE_URL}/sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId }),
  })
  
  if (!response.ok) {
    throw new Error(`Failed to create session: ${response.statusText}`)
  }
  const res: CreateSessionResponse = await response.json()
  console.log('Created session response:', res);
  
  return res.session
}

/**
 * Send a message to the chat session
 */
export async function sendChatMessage(sessionId: string, content: string): Promise<SendMessageResponse> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ sender: 'user', content }),
  })
  
  if (!response.ok) {
    throw new Error(`Failed to send message: ${response.statusText}`)
  }
  
  const data = await response.json()
  console.log('Send message response:', data)
  
  return data
}

/**
 * End a chat session and get summary
 */
export async function endChatSession(sessionId: string): Promise<SessionSummary> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/end`, {
    method: 'POST',
  })
  
  if (!response.ok) {
    throw new Error(`Failed to end session: ${response.statusText}`)
  }
  
  return await response.json()
}

/**
 * Get session summary
 */
export async function getSessionSummary(sessionId: string): Promise<SessionSummary> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/summary`)
  
  if (!response.ok) {
    throw new Error(`Failed to get session summary: ${response.statusText}`)
  }
  
  return await response.json()
}