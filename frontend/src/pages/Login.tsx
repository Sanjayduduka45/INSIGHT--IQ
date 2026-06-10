import { useState } from 'react'
import { useAuth } from '../lib/auth'
import { LogIn, UserPlus, ShieldCheck, Mail, Lock, AlertCircle } from 'lucide-react'

interface Props {
  onSuccess: () => void
}

export default function Login({ onSuccess }: Props) {
  const { login, signup, continueAsGuest, isMock } = useAuth()
  const [isSignUp, setIsSignUp] = useState(false)
  const [isForgot, setIsForgot] = useState(false)
  
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

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
          setTimeout(() => onSuccess(), 1000)
        } catch (signUpErr: any) {
          if (signUpErr.message === 'CONFIRM_EMAIL_REQUIRED') {
            setSuccessMsg('Registration successful! Please check your email to confirm your account before signing in.')
          } else {
            throw signUpErr
          }
        }
      } else {
        await login(email, password)
        onSuccess()
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  };

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
      // simulate forgot password
      await new Promise((resolve) => setTimeout(resolve, 800))
      setSuccessMsg('If this email is registered, we have sent instructions to reset your password.')
    } catch (err: any) {
      setError(err.message || 'Failed to submit reset request.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-6 relative overflow-hidden font-sans">
      {/* Background gradients */}
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] rounded-full bg-blue-900/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] rounded-full bg-indigo-900/20 blur-[120px] pointer-events-none" />

      {/* Main Container */}
      <div className="w-full max-w-md bg-slate-900/70 backdrop-blur-xl border border-slate-800 rounded-2xl shadow-2xl p-8 relative z-10 animate-scale-in">
        {/* Mock Banner */}
        {isMock && (
          <div className="mb-6 flex items-center gap-2 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl text-xs text-blue-400">
            <ShieldCheck size={16} className="text-blue-400 flex-shrink-0" />
            <span>
              <strong>Demo Environment</strong>: Enter any mock email and a 6+ char password to authenticate.
            </span>
          </div>
        )}

        <div className="text-center mb-8">
          <img src="/logo.png" alt="InsightIQ Logo" className="w-12 h-12 object-contain rounded-2xl mx-auto mb-4 shadow-lg shadow-blue-500/20" />
          <h2 className="text-2xl font-black tracking-tight text-white">
            {isForgot ? 'Reset Password' : isSignUp ? 'Create Account' : 'Welcome to InsightIQ'}
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            {isForgot ? 'Restore access to your workspace' : isSignUp ? 'Get started with AI data analytics' : 'Sign in to access your data platform'}
          </p>
        </div>

        {error && (
          <div className="mb-6 flex items-start gap-2.5 p-3.5 bg-red-500/10 border border-red-500/20 rounded-xl text-xs text-red-400 animate-fade-in">
            <AlertCircle size={16} className="text-red-400 mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="mb-6 flex items-start gap-2.5 p-3.5 bg-green-500/10 border border-green-500/20 rounded-xl text-xs text-green-400 animate-fade-in">
            <ShieldCheck size={16} className="text-green-400 mt-0.5 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {isForgot ? (
          <form onSubmit={handleForgotSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <span className="absolute left-3 top-3.5 text-slate-500">
                  <Mail size={16} />
                </span>
                <input
                  type="email"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl font-bold text-sm shadow-lg shadow-blue-500/10 transition-all flex items-center justify-center gap-2 cursor-pointer mt-6"
            >
              {loading ? 'Submitting...' : 'Send Reset Link'}
            </button>

            <div className="text-center mt-6">
              <button
                type="button"
                onClick={() => {
                  setIsForgot(false)
                  setError(null)
                  setSuccessMsg(null)
                }}
                className="text-xs font-semibold text-slate-400 hover:text-white transition-colors cursor-pointer"
              >
                Back to Sign In
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <span className="absolute left-3 top-3.5 text-slate-500">
                  <Mail size={16} />
                </span>
                <input
                  type="email"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                  required
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
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
                    className="text-xs text-blue-400 hover:text-blue-300 font-medium cursor-pointer"
                  >
                    Forgot?
                  </button>
                )}
              </div>
              <div className="relative">
                <span className="absolute left-3 top-3.5 text-slate-500">
                  <Lock size={16} />
                </span>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                  required
                />
              </div>
            </div>

            {isSignUp && (
              <div className="animate-slide-up">
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Confirm Password
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-3.5 text-slate-500">
                    <Lock size={16} />
                  </span>
                  <input
                    type="password"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                    required
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl font-bold text-sm shadow-lg shadow-blue-500/10 transition-all flex items-center justify-center gap-2 cursor-pointer mt-6"
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

            {!isSignUp && (
              <>
                <div className="relative flex py-4 items-center">
                  <div className="flex-grow border-t border-slate-800"></div>
                  <span className="flex-shrink mx-4 text-slate-500 text-xs uppercase font-semibold">Or</span>
                  <div className="flex-grow border-t border-slate-800"></div>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    continueAsGuest()
                    onSuccess()
                  }}
                  className="w-full py-3 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl font-bold text-sm border border-slate-700 hover:border-slate-600 transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  Continue as Guest
                </button>
              </>
            )}

            <div className="text-center mt-6">
              <button
                type="button"
                onClick={() => {
                  setIsSignUp(!isSignUp)
                  setError(null)
                  setSuccessMsg(null)
                }}
                className="text-xs font-semibold text-slate-400 hover:text-white transition-colors cursor-pointer"
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
