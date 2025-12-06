import { useState, useEffect } from 'react'
import { useNavigate } from '@tanstack/react-router'
import CalendarView from './components/CalendarView'
import WelcomeHeader from './components/WelcomeHeader'
import SessionHistory from './components/SessionHistory'
import MoodCheckIn from './components/MoodCheckIn'
import { useDashboardData } from '@/hooks/useDashboardData'


const DashboardLayout = () => {
  const [userId, setUserId] = useState<string | null>(null)
  const navigate = useNavigate()
  
  // Initialize userId from localStorage on component mount
  useEffect(() => {
    const storedUserId = localStorage.getItem('userId')
    if (storedUserId) {
      setUserId(storedUserId)
    } else {
      // Redirect to signup if no user ID found
      navigate({ to: '/signup' })
    }
  }, [])
  
  console.log('DashboardLayout: current userId =', userId)
  
  // Fetch all dashboard data using React Query (only when userId is available)
  const {
    isLoading,
    isError,
    errors,
    user,
    weather,
    moodEntries,
    sessions,
  } = useDashboardData(userId || '')

  // Don't render anything until userId is loaded
  if (!userId) {
    return (
      <div className="h-screen bg-[#F6F4F2] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  // Show loading state
  if (isLoading) {
    return (
      <div className="h-screen bg-[#F6F4F2] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  // Show error state
  if (isError) {
    return (
      <div className="h-screen bg-[#F6F4F2] flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-4">⚠️ Error Loading Dashboard</div>
          <div className="space-y-2">
            {errors.map((error, index) => (
              <p key={index} className="text-red-600 text-sm">
                {error?.message || 'Unknown error occurred'}
              </p>
            ))}
          </div>
          <button 
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  // Prepare data for components (with fallbacks)
  const userData = user ? { name: user.name } : { name: 'Loading...' }
  const weatherData = weather ? {
    temperature: weather.temperature,
    description: weather.description
  } : { temperature: 0, description: 'Loading...' }

  return (
    <div className="h-screen bg-[#F6F4F2]">
      {/* Outer container must allow children to shrink */}
      <div className="max-w-7xl mx-auto p-6 h-full flex flex-col min-h-0">
        {/* Header (auto height) */}
        <div className="mb-6">
          <WelcomeHeader user={userData} weather={weatherData} />
        </div>

        {/* Main grid area fills remaining height */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
          {/* LEFT COLUMN */}
          <div className="lg:col-span-2 gap-6 h-full min-h-0">
            <SessionHistory sessions={sessions || []} />
          </div>

          {/* RIGHT COLUMN */}
          <div className="flex flex-col gap-6 h-full min-h-0">
            <div className="flex-1">
              <MoodCheckIn moodHistory={moodEntries || []} userId={userId || ''} />
            </div>
            <div className="flex-2">
              <CalendarView calendarData={moodEntries || []}/>
              {/* <CheckinTabs calendarData={moodEntries || []}  /> */}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardLayout