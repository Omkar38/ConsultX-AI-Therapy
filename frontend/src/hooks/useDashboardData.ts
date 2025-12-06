import { useQuery } from '@tanstack/react-query'
import { fetchUser, fetchWeather, fetchMoodEntries, fetchSessions } from '@/lib/api'
import type { User, Weather, Session } from '@/lib/api'
import type { MoodEntry } from '@/types/dashboard'

// Query key factory for consistent cache keys
export const dashboardKeys = {
  all: ['dashboard'] as const,
  user: (userId: string) => [...dashboardKeys.all, 'user', userId] as const,
  weather: () => [...dashboardKeys.all, 'weather'] as const,
  moodEntries: (userId: string) => [...dashboardKeys.all, 'mood-entries', userId] as const,
  sessions: (userId: string) => [...dashboardKeys.all, 'sessions', userId] as const,
}

/**
 * Hook to fetch user profile data
 */
export function useUser(userId: string) {
  return useQuery({
    queryKey: dashboardKeys.user(userId),
    queryFn: () => fetchUser(userId),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!userId, // Only fetch if userId is provided
  })
}

/**
 * Hook to fetch weather data
 */
export function useWeather() {
  return useQuery({
    queryKey: dashboardKeys.weather(),
    queryFn: fetchWeather,
    staleTime: 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus: false, // Weather doesn't change that often
  })
}

/**
 * Hook to fetch mood entries for a user
 */
export function useMoodEntries(userId: string) {
  return useQuery({
    queryKey: dashboardKeys.moodEntries(userId),
    queryFn: () => fetchMoodEntries(userId),
    staleTime: 2 * 60 * 1000, // 2 minutes
    enabled: !!userId, // Only fetch if userId is provided
  })
}

/**
 * Hook to fetch sessions for a user
 */
export function useSessions(userId: string) {
  return useQuery({
    queryKey: dashboardKeys.sessions(userId),
    queryFn: () => fetchSessions(userId),
    staleTime: 30 * 1000, // 30 seconds - sessions might update more frequently
    enabled: !!userId, // Only fetch if userId is provided
  })
}

/**
 * Combined hook to fetch all dashboard data
 * Returns loading state, error state, and all data
 */
export function useDashboardData(userId: string) {
  const userQuery = useUser(userId)
  const weatherQuery = useWeather()
  const moodEntriesQuery = useMoodEntries(userId)
  const sessionsQuery = useSessions(userId)

  const isLoading = userQuery.isLoading || weatherQuery.isLoading || 
                   moodEntriesQuery.isLoading || sessionsQuery.isLoading
  
  const isError = userQuery.isError || weatherQuery.isError || 
                 moodEntriesQuery.isError || sessionsQuery.isError
  
  const errors = [
    userQuery.error,
    weatherQuery.error,
    moodEntriesQuery.error,
    sessionsQuery.error,
  ].filter(Boolean)

  return {
    // Loading states
    isLoading,
    isError,
    errors,
    
    // Individual query states
    userQuery,
    weatherQuery,
    moodEntriesQuery,
    sessionsQuery,
    
    // Data (will be undefined if loading or error)
    user: userQuery.data,
    weather: weatherQuery.data,
    moodEntries: moodEntriesQuery.data,
    sessions: sessionsQuery.data,
  }
}