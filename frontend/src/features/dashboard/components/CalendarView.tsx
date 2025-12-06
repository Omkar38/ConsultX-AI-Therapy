import type { MoodEntry } from "@/types/dashboard"

interface CalendarViewProps {
  calendarData: MoodEntry[]
}

const CalendarView = ({ calendarData }: CalendarViewProps) => {
  const currentDate = new Date()
  const currentMonth = currentDate.getMonth()
  const currentYear = currentDate.getFullYear()
  
  // Get first day of month and number of days
  const firstDay = new Date(currentYear, currentMonth, 1)
  const lastDay = new Date(currentYear, currentMonth + 1, 0)
  const daysInMonth = lastDay.getDate()
  const startingDayOfWeek = firstDay.getDay() // 0 = Sunday
  
  // Create array of all dates in month
  const days = []
  
  // Add empty cells for days before month starts
  for (let i = 0; i < startingDayOfWeek; i++) {
    days.push(null)
  }
  
  // Add all days of the month
  for (let day = 1; day <= daysInMonth; day++) {
    days.push(day)
  }
  
  const monthName = currentDate.toLocaleDateString('en-US', { month: 'long' })
  
  const hasMoodEntry = (day: number): boolean => {
    const dateStr = `${currentYear}-${(currentMonth + 1).toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`
    return calendarData.some(entry => entry.date === dateStr)
  }
  
  const isToday = (day: number): boolean => {
    return day === currentDate.getDate() && 
           currentMonth === currentDate.getMonth() && 
           currentYear === currentDate.getFullYear()
  }
  
  const getConsecutiveDays = (): number => {
    let consecutive = 0
    const today = new Date()
    
    for (let i = 0; i < 30; i++) {
      const checkDate = new Date(today)
      checkDate.setDate(today.getDate() - i)
      const dateStr = checkDate.toISOString().split('T')[0]
      
      const hasEntry = calendarData.some(entry => entry.date === dateStr)
      if (hasEntry) {
        consecutive++
      } else {
        break
      }
    }
    
    return consecutive
  }
  
  const streak = getConsecutiveDays()
  
  return (
    <div className="bg-white rounded-xl shadow-sm p-6 h-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Check-in Calendar</h3>
        <div className="flex items-center gap-2 text-sm">
          <div className="w-3 h-3 bg-[#6BAF7A] rounded-full"></div>
          <span className="text-gray-600">Mood logged</span>
        </div>
      </div>
      
      {/* Streak Counter */}
      <div className="mb-2 p-3 bg-[#F6F4F2] rounded-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-[#E7C45B]" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.214.33-.403.713-.57 1.116-.334.804-.614 1.768-.84 2.734a31.365 31.365 0 00-.613 3.58 2.64 2.64 0 01-.945-1.067c-.328-.68-.398-1.534-.398-2.654A1 1 0 005.05 6.05 6.981 6.981 0 003 11a7 7 0 1011.95-4.95c-.592-.591-.98-.985-1.348-1.467-.363-.476-.724-1.063-1.207-2.03zM12.12 15.12A3 3 0 017 13s.879.5 2.5.5c0-1 .5-4 1.25-4.5.5 1 .786 1.293 1.371 1.879A2.99 2.99 0 0113 13a2.99 2.99 0 01-.879 2.121z" clipRule="evenodd" />
            </svg>
            <span className="font-medium text-gray-900">{streak} day streak</span>
          </div>
          {streak > 0 && (
            <span className="text-xs text-[#6BAF7A]">Keep it up! 🎉</span>
          )}
        </div>
      </div>
      
      {/* Month header */}
      <div className="text-center mb-2">
        <h4 className="text-base font-medium text-gray-900">{monthName} {currentYear}</h4>
      </div>
      
      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-0.5">
        {/* Day headers */}
        {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(dayName => (
          <div key={dayName} className="text-center text-xs font-medium text-gray-500">
            {dayName}
          </div>
        ))}
        
        {/* Calendar days */}
        {days.map((day, index) => (
          <div key={index} className="aspect-auto flex items-center justify-center">
            {day && (
              <div className="relative w-8 h-8 flex items-center justify-center">
                {/* Green circle for days with mood entries */}
                {hasMoodEntry(day) && (
                  <div className="absolute inset-0 w-8 h-8 bg-[#6BAF7A] rounded-full opacity-20"></div>
                )}
                {hasMoodEntry(day) && (
                  <div className="absolute inset-0 w-8 h-8 border-2 border-[#6BAF7A] rounded-full"></div>
                )}
                
                {/* Today indicator */}
                {isToday(day) && (
                  <div className="absolute inset-0 w-8 h-8 bg-[#4A90A0] rounded-full opacity-20"></div>
                )}
                
                {/* Day number */}
                <span className={`relative text-sm font-medium ${
                  isToday(day) 
                    ? 'text-[#4A90A0] font-bold' 
                    : hasMoodEntry(day)
                      ? 'text-[#6BAF7A] font-semibold'
                      : 'text-gray-700'
                }`}>
                  {day}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Legend */}
      <div className="mt-4 flex justify-center gap-4 text-xs text-gray-600">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 border-2 border-[#4A90A0] rounded-full"></div>
          <span>Today</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 border-2 border-[#6BAF7A] rounded-full bg-[#6BAF7A] bg-opacity-20"></div>
          <span>Mood logged</span>
        </div>
      </div>
    </div>
  )
}

export default CalendarView;