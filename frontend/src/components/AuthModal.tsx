import React, { useState, useEffect } from 'react'
import { useAuth } from '../lib/auth'
import { LogIn, UserPlus, ShieldCheck, Mail, Lock, AlertCircle, X } from 'lucide-react'

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
  initialTab: 'login' | 'signup'
  onSuccess: () => void
}

export default function AuthModal({
  isOpen,
  onClose,
  initialTab,
  onSuccess,
}: AuthModalProps) {
  const { login, signup, isMock } = useAuth()
  const [isSignUp, setIsSignUp] = useState(initialTab === 'signup')
  const [isForgot, setIsForgot] = useState(false)
  
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  // Sync initial tab when changed
  useEffect(() => {
    setIsSignUp(initialTab === 'signup')
    setIsForgot(false)
    setError(null)
    setSuccessMsg(null)
  }, [initialTab, isOpen])

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccessMsg(null)

    if (!email || !password) {
      setError('Please fill in all fields.')
      return
    }

    if (isSignUp && password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      if (isSignUp) {
        try {
          await signup(email, password)
          setSuccessMsg('Account created successfully!')
          setTimeout(() => {
            onSuccess()
            onClose()
          }, 1000)
        } catch (signUpErr: any) {
          if (signUpErr.message === 'CONFIRM_EMAIL_REQUIRED') {
            setSuccessMsg('Registration successful! Please check your email to confirm your account.')
          } else {
            throw signUpErr
          }
        }
      } else {
        await login(email, password)
        onSuccess()
        onClose()
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccessMsg(null)
    
    if (!email) {
      setError('Please provide your email address.')
      return
    }

    setLoading(true)
    try {
      await new Promise((resolve) => setTimeout(resolve, 800))
      setSuccessMsg('If this email is registered, we have sent instructions to reset your password.')
    } catch (err: any) {
      setError(err.message || 'Failed to submit reset request.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm transition-opacity" 
        onClick={onClose} 
      />

      {/* Modal Box */}
      <div className="relative w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-scale-in z-10 p-6 sm:p-8">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer"
        >
          <X size={18} />
        </button>

        {/* Demo Mode Notice */}
        {isMock && (
          <div className="mb-6 flex items-start gap-2.5 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl text-xs text-blue-600 dark:text-blue-400">
            <ShieldCheck size={16} className="flex-shrink-0 mt-0.5" />
            <span>
              <strong>Demo Mode</strong>: Enter any mock email and a 6+ char password to authenticate.
            </span>
          </div>
        )}

        <div className="text-center mb-6">
          <img src="/logo.png" alt="InsightIQ Logo" className="w-10 h-10 object-contain rounded-xl mx-auto mb-3 shadow-md" />
          <h2 className="text-xl font-extrabold text-slate-900 dark:text-white">
            {isForgot ? 'Reset Password' : isSignUp ? 'Create Account' : 'Welcome to InsightIQ'}
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {isForgot ? 'Restore access to your workspace' : isSignUp ? 'Get started with AI data analytics' : 'Sign in to access your data platform'}
          </p>
        </div>

        {error && (
          <div className="mb-4 flex items-start gap-2.5 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-xs text-red-600 dark:text-red-400 animate-fade-in">
            <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="mb-4 flex items-start gap-2.5 p-3 bg-green-500/10 border border-green-500/20 rounded-xl text-xs text-green-605 dark:text-green-400 animate-fade-in">
            <ShieldCheck size={16} className="mt-0.5 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {isForgot ? (
          <form onSubmit={handleForgotSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <span className="absolute left-3 top-3 text-slate-400">
                  <Mail size={16} />
                </span>
                <input
                  type="email"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 rounded-xl text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn btn-primary py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer mt-6"
            >
              {loading ? 'Submitting...' : 'Send Reset Link'}
            </button>

            <div className="text-center mt-4">
              <button
                type="button"
                onClick={() => {
                  setIsForgot(false)
                  setError(null)
                  setSuccessMsg(null)
                }}
                className="text-xs font-semibold text-slate-500 dark:text-slate-400 hover:text-slate-905 dark:hover:text-white transition-colors cursor-pointer"
              >
                Back to Sign In
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <span className="absolute left-3 top-3 text-slate-400">
                  <Mail size={16} />
                </span>
                <input
                  type="email"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 rounded-xl text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                  required
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Password
                </label>
                {!isSignUp && (
                  <button
                    type="button"
                    onClick={() => {
                      setIsForgot(true)
                      setError(null)
                      setSuccessMsg(null)
                    }}
                    className="text-xs text-blue-600 dark:text-blue-450 hover:underline font-semibold cursor-pointer"
                  >
                    Forgot?
                  </button>
                )}
              </div>
              <div className="relative">
                <span className="absolute left-3 top-3 text-slate-400">
                  <Lock size={16} />
                </span>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 rounded-xl text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                  required
                />
              </div>
            </div>

            {isSignUp && (
              <div className="animate-slide-up">
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                  Confirm Password
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-3 text-slate-400">
                    <Lock size={16} />
                  </span>
                  <input
                    type="password"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 rounded-xl text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                    required
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full btn btn-primary py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer mt-6"
            >
              {loading ? (
                'Processing...'
              ) : isSignUp ? (
                <>
                  <UserPlus size={16} />
                  Sign Up
                </>
              ) : (
                <>
                  <LogIn size={16} />
                  Sign In
                </>
              )}
            </button>

            <div className="text-center mt-4">
              <button
                type="button"
                onClick={() => {
                  setIsSignUp(!isSignUp)
                  setError(null)
                  setSuccessMsg(null)
                }}
                className="text-xs font-semibold text-slate-550 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors cursor-pointer"
              >
                {isSignUp ? 'Already have an account? Sign In' : "Don't have an account? Sign Up"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
