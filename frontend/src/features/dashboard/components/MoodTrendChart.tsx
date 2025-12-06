import type { MoodEntry } from '@/types/dashboard'
import { getMoodEmoji } from '../utils'


const MoodTrendsChart = ({ moodHistory }: { moodHistory: MoodEntry[] }) => {
  const last7Days = moodHistory.slice(0, 7).reverse()
  
  // Generate SVG path for the line chart
  const generatePath = () => {
    if (last7Days.length === 0) return ''
    
    const chartWidth = 280
    const chartHeight = 80
    const pointSpacing = chartWidth / (last7Days.length - 1)
    
    let path = ''
    
    last7Days.forEach((entry, index) => {
      const x = index * pointSpacing
      const y = chartHeight - ((entry.mood - 1) / 4) * chartHeight // Scale 1-5 to chart height
      
      if (index === 0) {
        path += `M ${x} ${y}`
      } else {
        path += ` L ${x} ${y}`
      }
    })
    
    return path
  }
  
  const chartPath = generatePath()
  
  return (
    <div className="bg-white rounded-xl p-6 max-h-full">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Mood Trends</h3>
      
      <div className="space-y-4">
        {/* Line Chart */}
        <div className="relative h-20">
          <svg 
            width="100%" 
            height="100%" 
            viewBox="0 0 280 80" 
            className="overflow-visible"
          >
            {/* Background grid lines */}
            <defs>
              <pattern id="grid" width="56" height="20" patternUnits="userSpaceOnUse">
                <path d="M 56 0 L 0 0 0 20" fill="none" stroke="#F3F4F6" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
            
            {/* Mood level reference lines */}
            {[1, 2, 3, 4, 5].map(level => {
              const y = 80 - ((level - 1) / 4) * 80
              return (
                <line
                  key={level}
                  x1="0"
                  y1={y}
                  x2="280"
                  y2={y}
                  stroke="#D8EFE8"
                  strokeWidth="1"
                  strokeDasharray="2,2"
                />
              )
            })}
            
            {/* Main trend line */}
            {chartPath && (
              <path
                d={chartPath}
                fill="none"
                stroke="#4A90A0"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}
            
            {/* Data points */}
            {last7Days.map((entry, index) => {
              const x = index * (280 / (last7Days.length - 1))
              const y = 80 - ((entry.mood - 1) / 4) * 80
              
              return (
                <g key={entry.date}>
                  {/* Background circle for emoji */}
                  <circle
                    cx={x}
                    cy={y}
                    r="6"
                    fill="white"
                    stroke="#4A90A0"
                    strokeWidth="2"
                  />
                  {/* Mood emoji */}
                  <text
                    x={x}
                    y={y + 1}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontSize="20"
                    className="pointer-events-none"
                  >
                    {getMoodEmoji(entry.mood)}
                  </text>
                </g>
              )
            })}
          </svg>
        </div>
        
        {/* Date labels */}
        <div className="flex justify-between text-xs text-gray-500 px-1">
          {last7Days.map((entry) => (
            <span key={entry.date} className="text-center">
              {new Date(entry.date).toLocaleDateString('en-US', { weekday: 'short' })}
            </span>
          ))}
        </div>
        
        {/* Mood scale reference */}
        <div className="flex justify-between items-center text-xs text-gray-400 mt-2 px-1">
          <span>😔 Very Low</span>
          <span>😊 Great</span>
        </div>
      </div>
    </div>
  )
}

export default MoodTrendsChart;