import { getTimeBasedGreeting } from '../utils'


interface WelcomeHeaderProps {
  user: {
    name: string
  }
  weather: {
    temperature: number
    description: string
  }
}

const WelcomeHeader = ( { user, weather }: WelcomeHeaderProps) => {
  const greeting = getTimeBasedGreeting()
  
  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-medium text-gray-900 mb-1">
            {greeting}, {user.name}
          </h1>
          <p className="text-gray-600 text-md">
            Welcome back to your wellness journey
          </p>
        </div>
        
        {/* Weather Widget */}
        <div className="flex items-center gap-3 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.003 4.003 0 003 15z" />
            </svg>
            <span>{weather.temperature}°F</span>
          </div>
          <span>{weather.description}</span>
        </div>
      </div>
    </div>
  )
}


export default WelcomeHeader;