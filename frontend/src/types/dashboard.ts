export type MoodLevel = 1 | 2 | 3 | 4 | 5

export interface MoodEntry {
  date: string
  mood: MoodLevel
  note?: string
}

export interface DashboardData {
  userName: string,
  moodEntries: MoodEntry[]
  sessions: Session[]
  recommendedActivities: string[]
}
