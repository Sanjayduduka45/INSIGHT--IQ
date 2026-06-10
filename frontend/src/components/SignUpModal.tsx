import { X, CheckCircle2, Shield } from 'lucide-react'

interface SignUpModalProps {
  isOpen: boolean
  onClose: () => void
  onOpenLogin: () => void
  onOpenSignUp: () => void
}

export default function SignUpModal({
  isOpen,
  onClose,
  onOpenLogin,
  onOpenSignUp,
}: SignUpModalProps) {
  if (!isOpen) return null

  const benefits = [
    'Save unlimited projects',
    'Export executive reports (PDF, PPT)',
    'Share interactive dashboards',
    'Secure cloud storage integration',
    'Real-time team collaboration',
  ]

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
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

        {/* Brand/Header */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-blue-600/10 text-blue-600 dark:text-blue-400 mx-auto mb-4">
            <Shield size={24} />
          </div>
          <h2 className="text-xl font-extrabold text-slate-900 dark:text-white">
            Unlock Full InsightIQ
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Access premium analytical tools and persistent cloud workspaces.
          </p>
        </div>

        {/* Benefits Checklist */}
        <div className="space-y-3 bg-slate-50 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-100 dark:border-slate-800 mb-6">
          {benefits.map((benefit, i) => (
            <div key={i} className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
              <CheckCircle2 className="text-emerald-500 flex-shrink-0" size={16} />
              <span>{benefit}</span>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="space-y-3">
          {/* Regular Signup */}
          <button
            onClick={() => {
              onClose()
              onOpenSignUp()
            }}
            className="w-full btn btn-primary py-2.5 rounded-xl font-bold text-sm shadow-md cursor-pointer"
          >
            Sign Up
          </button>

          {/* Log In Link */}
          <div className="text-center mt-4">
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Already have an account?{' '}
              <button
                onClick={() => {
                  onClose()
                  onOpenLogin()
                }}
                className="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline cursor-pointer"
              >
                Login
              </button>
            </span>
          </div>
        </div>

      </div>
    </div>
  )
}
