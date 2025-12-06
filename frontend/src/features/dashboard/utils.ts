export const getTimeBasedGreeting = () => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

export const getMoodEmoji = (moodLevel: number) => {
  switch (moodLevel) {
    case 1:
      return '😔'
    case 2:
      return '😕'
    case 3:
      return '😐'
    case 4:
      return '🙂'
    case 5:
      return '😊'
    default:
      return '😐'
  }
}

export const getMoodLabel = (mood: number) => {
    switch (mood) {
        case 1:
            return 'Very Low'
        case 2:
            return 'Low'
        case 3:
            return 'Okay'
        case 4:
            return 'Good'
        case 5:
            return 'Great'
        default:
            return 'Unknown'
    }
}