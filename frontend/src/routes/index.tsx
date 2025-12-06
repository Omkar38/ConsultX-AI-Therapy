import { createFileRoute, Link } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: HomePage,
})

export function HomePage() {
  return (
    <div className="min-h-screen bg-[#F6F4F2] flex items-center justify-center p-4">
      <div className="text-center max-w-2xl">
        <div className="mb-12">
          <h1 className="text-4xl font-medium text-gray-900 mb-4">
            Welcome to ConsultX
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Your trusted companion for mental wellness and personal growth
          </p>
          <p className="text-base text-gray-600 leading-relaxed">
            Take control of your mental health journey with personalized tools, 
            guided exercises, and supportive resources designed to help you thrive.
          </p>
        </div>

        <div className="space-y-4 sm:space-y-0 sm:space-x-4 sm:flex sm:justify-center">
          <Link
            viewTransition
            to="/signup"
            className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-[#4A90A0] hover:bg-[#3A7080] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#4A90A0] transition-colors w-full sm:w-auto"
          >
            Get Started
          </Link>
          {/* <Link
            to="/login"
            className="inline-flex items-center justify-center px-8 py-3 border-2 border-[#4A90A0] text-base font-medium rounded-lg text-[#4A90A0] bg-transparent hover:bg-[#4A90A0] hover:text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#4A90A0] transition-colors w-full sm:w-auto"
          >
            Sign In
          </Link> */}
        </div>

        <div className="mt-12 pt-8 border-t border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
            <div className="text-center">
              <div className="w-12 h-12 bg-[#D8EFE8] rounded-lg flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-[#4A90A0]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Daily Check-ins</h3>
              <p className="text-gray-600">Track your mood and emotions with gentle, guided prompts</p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-[#E3E2F0] rounded-lg flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-[#6879A1]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Mindful Exercises</h3>
              <p className="text-gray-600">Breathing exercises and meditation practices for inner calm</p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-[#D8EFE8] rounded-lg flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-[#70A8A2]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Resource Library</h3>
              <p className="text-gray-600">Access helpful articles, guides, and tools for mental wellness</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
