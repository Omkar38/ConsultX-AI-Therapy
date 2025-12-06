import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'

export const Route = createFileRoute('/signup')({  
  component: SignupPage,
})

function SignupPage() {
  const [userId, setUserId] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isLoading, setIsLoading] = useState(false)

  const navigate = useNavigate()
 
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.target
    setUserId(value)
    
    // Clear error when user starts typing
    if (errors.userId) {
      setErrors(prev => ({ ...prev, userId: '' }))
    }
  }

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!userId.trim()) {
      newErrors.userId = 'User ID is required'
    } else if (userId.length < 3) {
      newErrors.userId = 'User ID must be at least 3 characters'
    } else if (!/^[a-zA-Z0-9_]+$/.test(userId)) {
      newErrors.userId = 'User ID can only contain letters, numbers, and underscores'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) {
      return
    }
    setIsLoading(true)
    try {
      // Simulate API call to register user ID
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Store user ID in localStorage for now
      localStorage.setItem('userId', userId)
      
      // Navigate to dashboard
      navigate({ to: '/dashboard' })
      
    } catch (err: any) {
      setErrors({ general: err?.message || 'Something went wrong. Please try again.' })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#F6F4F2] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-xl shadow-sm p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-2xl font-medium text-gray-900 mb-2">
              Enter your User ID
            </h1>
            <p className="text-gray-600 text-base">
              Choose a unique identifier to get started
            </p>
          </div>

          {/* General Error Message */}
          {errors.general && (
            <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-100">
              <p className="text-[#C46262] text-sm">{errors.general}</p>
            </div>
          )}

          {/* Signup Form */}
          <form onSubmit={handleSubmit} className="space-y-6">

            {/* User ID */}
            <div>
                <label htmlFor="userId" className="block text-sm font-medium text-gray-700 mb-2">
                  User ID
                </label>
                <input
                  id="userId"
                  name="userId"
                  type="text"
                  autoComplete="username"
                  required
                  value={userId}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 rounded-md border ${errors.userId ? 'border-[#C46262]' : 'border-gray-300'} bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#4A90A0] focus:border-transparent transition-colors`}
                  placeholder="Enter your unique user ID"
                />
                {errors.userId && <p className="mt-1 text-sm text-[#C46262]">{errors.userId}</p>}
                <p className="mt-1 text-sm text-gray-500">At least 3 characters, letters, numbers, and underscores only</p>
              </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-[#4A90A0] hover:bg-[#3A7080] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#4A90A0] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Confirming...
                </div>
              ) : (
                'Continue to Dashboard'
              )}
            </button>
          </form>

          {/* Login link */}
          <div className="mt-8 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <Link
                to="/login"
                className="font-medium text-[#4A90A0] hover:text-[#3A7080] transition-colors"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>

        {/* Support Link */}
        {/* <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            Need help?{' '}
            <a href="#" className="text-[#4A90A0] hover:text-[#3A7080] transition-colors">
              Contact support
            </a>
          </p>
        </div> */}
      </div>
    </div>
  )
}