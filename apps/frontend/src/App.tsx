/**
 * InsightIQ — Main Application Shell
 *
 * Layout: Top Header + (Fixed sidebar + main content area with page routing)
 */

import { useState, useEffect } from 'react'
import { Routes, Route, NavLink, useNavigate, Link } from 'react-router-dom'
import {
  Home as HomeIcon, Upload, BarChart3, AlertTriangle, TrendingUp,
  MessageSquare, Database, GitBranch,
  Settings, Menu, X, Download, LayoutDashboard, LogOut, Users
} from 'lucide-react'

// Pages
import HomePage from './pages/Home'
import UploadPage from './pages/Upload'
import KPIDashboard from './pages/KPIDashboard'
import AnomalyCenter from './pages/AnomalyCenter'
import ForecastCenter from './pages/ForecastCenter'
import AIChat from './pages/AIChat'
import DataQuality from './pages/DataQuality'
import CorrelationExplorer from './pages/CorrelationExplorer'
import ExecutiveReports from './pages/ExecutiveReports'
import SettingsPage from './pages/Settings'
import ExecutiveDashboard from './pages/ExecutiveDashboard'
import CustomerIntelligence from './pages/CustomerIntelligence'

// Marketing / Informational Pages
import FeaturesPage from './pages/Features'
import SolutionsPage from './pages/Solutions'
import AboutPage from './pages/About'

// Modals & Auth
import SignUpModal from './components/SignUpModal'
import AuthModal from './components/AuthModal'
import { useAuth } from './lib/auth'
import type { SafeAny } from './types'

const NAV_ITEMS = [
  { path: '/', icon: HomeIcon, label: 'Home' },
  { path: '/dashboard', icon: LayoutDashboard, label: 'Executive Dashboard' },
  { path: '/upload', icon: Upload, label: 'Upload Data' },
  { path: '/kpi', icon: BarChart3, label: 'KPI Dashboard' },
  { path: '/customer-intelligence', icon: Users, label: 'Customer Intelligence' },
  { path: '/anomalies', icon: AlertTriangle, label: 'Anomaly Center' },
  { path: '/forecast', icon: TrendingUp, label: 'Forecast' },
  { path: '/chat', icon: MessageSquare, label: 'AI Chat' },
  { path: '/quality', icon: Database, label: 'Data Quality' },
  { path: '/correlations', icon: GitBranch, label: 'Correlations' },
  { path: '/reports', icon: Download, label: 'Export Reports' },
]

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [datasetId, setDatasetId] = useState<string | null>(null)
  const [datasetName, setDatasetName] = useState<string>('')
  const [datasetMeta, setDatasetMeta] = useState<SafeAny>(null)
  
  // Modals & Splash states
  const [splashActive, setSplashActive] = useState(() => {
    return !sessionStorage.getItem('insightiq_splash_shown')
  })
  const [showSignUpModal, setShowSignUpModal] = useState(false)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [authModalTab, setAuthModalTab] = useState<'login' | 'signup'>('login')
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false)

  const navigate = useNavigate()
  const { user, isLoading, logout, continueAsGuest } = useAuth()

  // Close profile dropdown when clicking outside
  useEffect(() => {
    if (!profileDropdownOpen) return
    const closeDropdown = () => setProfileDropdownOpen(false)
    window.addEventListener('click', closeDropdown)
    return () => window.removeEventListener('click', closeDropdown)
  }, [profileDropdownOpen])

  // Intercepting guest access custom event listeners
  useEffect(() => {
    const handleTriggerSignUp = () => {
      setShowSignUpModal(true)
    }
    window.addEventListener('insightiq-trigger-signup', handleTriggerSignUp)
    return () => {
      window.removeEventListener('insightiq-trigger-signup', handleTriggerSignUp)
    }
  }, [])

  // Session auto-guest initiation on load
  useEffect(() => {
    if (!isLoading && !user) {
      continueAsGuest()
    }
  }, [isLoading, user, continueAsGuest])

  const handleDatasetLoaded = (id: string, name: string, meta: SafeAny) => {
    setDatasetId(id)
    setDatasetName(name)
    setDatasetMeta(meta)
    navigate('/')
  }

  const handleSplashComplete = () => {
    sessionStorage.setItem('insightiq_splash_shown', 'true')
    setSplashActive(false)
    navigate('/')
  }



  if (splashActive) {
    return <SplashScreen onComplete={handleSplashComplete} />
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          <span className="text-slate-400 text-xs font-semibold tracking-wider uppercase">Loading session...</span>
        </div>
      </div>
    )
  }

  const isGuest = user?.role === 'guest'

  return (
    <div className="flex flex-col min-h-screen" style={{ background: 'var(--color-bg)' }}>
      
      {/* ── Global Header ────────────────────────────────────────────── */}
      <header className="fixed top-0 left-0 w-full h-16 bg-white dark:bg-slate-900 border-b border-slate-100 dark:border-slate-800 z-40 flex items-center justify-between px-6 font-sans">
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2.5">
            <img src="/logo.png" alt="InsightIQ Logo" className="w-8 h-8 object-contain rounded-lg shadow-sm" />
            <span className="font-extrabold text-base tracking-tight text-slate-900 dark:text-white">
              InsightIQ
            </span>
          </Link>

          {/* Marketing Navigation */}
          <nav className="hidden md:flex items-center gap-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            <NavLink 
              to="/" 
              end
              className={({ isActive }) => `hover:text-blue-600 dark:hover:text-blue-400 transition-colors ${isActive ? 'text-blue-600 dark:text-blue-400' : ''}`}
            >
              Home
            </NavLink>
            <NavLink 
              to="/features" 
              className={({ isActive }) => `hover:text-blue-600 dark:hover:text-blue-400 transition-colors ${isActive ? 'text-blue-600 dark:text-blue-400' : ''}`}
            >
              Features
            </NavLink>
            <NavLink 
              to="/solutions" 
              className={({ isActive }) => `hover:text-blue-600 dark:hover:text-blue-400 transition-colors ${isActive ? 'text-blue-600 dark:text-blue-400' : ''}`}
            >
              Solutions
            </NavLink>
            <NavLink 
              to="/about" 
              className={({ isActive }) => `hover:text-blue-600 dark:hover:text-blue-400 transition-colors ${isActive ? 'text-blue-600 dark:text-blue-400' : ''}`}
            >
              About
            </NavLink>
          </nav>
        </div>

        {/* Authentication controls */}
        <div className="flex items-center gap-4">
          {isGuest ? (
            <div className="flex items-center gap-2.5">
              <button
                onClick={() => {
                  setAuthModalTab('login')
                  setShowAuthModal(true)
                }}
                className="btn btn-secondary px-3.5 py-1.5 text-xs rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 dark:text-white cursor-pointer"
              >
                Login
              </button>
              <button
                onClick={() => {
                  setAuthModalTab('signup')
                  setShowAuthModal(true)
                }}
                className="btn btn-primary px-3.5 py-1.5 text-xs rounded-xl cursor-pointer"
              >
                Sign Up
              </button>
            </div>
          ) : (
            <div className="relative">
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  setProfileDropdownOpen(!profileDropdownOpen);
                }}
                className="flex items-center gap-2.5 p-1.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-left cursor-pointer"
              >
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold shadow-md shadow-blue-500/10">
                  {user?.email ? user.email[0].toUpperCase() : 'U'}
                </div>
                <div className="hidden sm:block">
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate max-w-[120px]">
                    {localStorage.getItem('user_name') || (user?.email ? user.email.split('@')[0] : 'User')}
                  </span>
                </div>
              </button>

              {profileDropdownOpen && (
                <div className="absolute right-0 mt-2 w-52 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-lg py-1.5 z-50 animate-fade-in">
                  <div className="px-4 py-2 border-b border-slate-100 dark:border-slate-800 mb-1">
                    <div className="text-xs font-bold text-slate-800 dark:text-white truncate">
                      {user?.email}
                    </div>
                    <div className="text-[9px] uppercase font-bold text-blue-600 mt-0.5">
                      {user?.role} Access
                    </div>
                  </div>
                  
                  <Link
                    to="/settings"
                    onClick={() => setProfileDropdownOpen(false)}
                    className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                  >
                    <Settings size={14} className="text-slate-400" />
                    Settings & Preferences
                  </Link>
                  
                  <button
                    onClick={() => {
                      setProfileDropdownOpen(false);
                      logout();
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2 text-xs font-semibold text-red-650 hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors text-left border-t border-slate-100 dark:border-slate-800 mt-1"
                  >
                    <LogOut size={14} />
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      <div className="flex flex-1">
        {/* ── Sidebar ────────────────────────────────────────────────── */}
        <aside
          className={`sidebar transition-transform duration-300 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          {/* Navigation */}
          <nav className="sidebar-nav pt-4">
            {NAV_ITEMS.map(({ path, icon: Icon, label }) => (
              <NavLink
                key={path}
                to={path}
                end={path === '/'}
                className={({ isActive }) =>
                  `sidebar-link ${isActive ? 'active' : ''}`
                }
              >
                <Icon size={18} />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>

          {/* Active Dataset info */}
          <div className="p-4 border-t" style={{ borderColor: 'var(--color-border-light)' }}>
            {datasetId ? (
              <div className="text-xs">
                <div className="uppercase tracking-wider mb-1" style={{ color: 'var(--color-text-muted)', fontSize: '0.65rem' }}>
                  Active Dataset
                </div>
                <div className="font-semibold truncate" style={{ color: 'var(--color-text-primary)' }}>
                  {datasetName}
                </div>
                {datasetMeta && (
                  <div style={{ color: 'var(--color-text-secondary)' }}>
                    {datasetMeta.rows?.toLocaleString()} rows · {datasetMeta.columns} cols
                  </div>
                )}
              </div>
            ) : (
              <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                No dataset loaded
              </div>
            )}
          </div>
        </aside>

        {/* ── Main Content ───────────────────────────────────────────── */}
        <main className="page-wrapper flex-1">
          {/* Mobile menu toggle */}
          <button
            className="fixed top-4 left-4 z-50 p-2 rounded-lg lg:hidden"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          <Routes>
            <Route path="/" element={<HomePage datasetId={datasetId} onNavigate={(path: string) => navigate(path)} />} />
            <Route path="/dashboard" element={<ExecutiveDashboard datasetId={datasetId} />} />
            <Route path="/upload" element={<UploadPage onDatasetLoaded={handleDatasetLoaded} />} />
            <Route path="/kpi" element={<KPIDashboard datasetId={datasetId} />} />
            <Route path="/customer-intelligence" element={<CustomerIntelligence datasetId={datasetId} />} />
            <Route path="/anomalies" element={<AnomalyCenter datasetId={datasetId} />} />
            <Route path="/forecast" element={<ForecastCenter datasetId={datasetId} />} />
            <Route path="/chat" element={<AIChat datasetId={datasetId} />} />
            <Route path="/quality" element={<DataQuality datasetId={datasetId} />} />
            <Route path="/correlations" element={<CorrelationExplorer datasetId={datasetId} />} />
            <Route path="/reports" element={<ExecutiveReports datasetId={datasetId} />} />
            <Route path="/settings" element={<SettingsPage />} />

            {/* Marketing pages */}
            <Route path="/features" element={<FeaturesPage />} />
            <Route path="/solutions" element={<SolutionsPage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </main>
      </div>

      {/* ── Global Modals ────────────────────────────────────────────── */}
      <SignUpModal
        isOpen={showSignUpModal}
        onClose={() => setShowSignUpModal(false)}
        onOpenLogin={() => {
          setAuthModalTab('login')
          setShowAuthModal(true)
        }}
        onOpenSignUp={() => {
          setAuthModalTab('signup')
          setShowAuthModal(true)
        }}
      />

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        initialTab={authModalTab}
        onSuccess={() => navigate('/')}
      />
    </div>
  )
}

/* ── Splash Screen Component ────────────────────────────────────────── */

function SplashScreen({ onComplete }: { onComplete: () => void }) {
  const [step, setStep] = useState(0)

  useEffect(() => {
    const timers = [
      setTimeout(() => setStep(1), 600),   // Intelligence Engine ready
      setTimeout(() => setStep(2), 1200),  // Data Analysis ready
      setTimeout(() => setStep(3), 1800),  // Forecast Engine ready
      setTimeout(() => setStep(4), 2400),  // Executive Reporting ready
      setTimeout(() => setStep(5), 2800),  // Ready to fade out
      setTimeout(() => onComplete(), 3200) // Finish
    ]
    return () => timers.forEach(clearTimeout)
  }, [onComplete])

  return (
    <div className="fixed inset-0 bg-slate-950 flex flex-col items-center justify-center z-[200] text-white select-none animate-fade-in font-sans">
      {/* Background Orbs */}
      <div className="absolute top-1/4 left-1/4 w-[40vw] h-[40vw] rounded-full bg-blue-900/10 blur-[150px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[40vw] h-[40vw] rounded-full bg-indigo-900/10 blur-[150px] pointer-events-none" />

      <div className="flex flex-col items-center max-w-sm px-6 text-center z-10 space-y-8">
        {/* Logo and Name */}
        <div className="flex flex-col items-center gap-3">
          <div className="relative w-24 h-24 rounded-3xl bg-slate-900 border border-slate-800 flex items-center justify-center p-4 shadow-2xl shadow-blue-500/10 group animate-pulse-slow">
            {/* Spinning accent border */}
            <div className="absolute inset-0 rounded-3xl border border-dashed border-blue-500/30 animate-spin" style={{ animationDuration: '12s' }} />
            <img src="/logo.png" alt="InsightIQ Logo" className="w-16 h-16 object-contain rounded-2xl relative z-10" />
          </div>
          <h1 className="text-3xl font-black tracking-tight mt-4 bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            InsightIQ
          </h1>
          <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider">
            Transforming Data Into Decisions
          </p>
        </div>

        {/* Loading Readiness Steps */}
        <div className="w-full text-left space-y-3 bg-slate-900/40 backdrop-blur-xl border border-slate-900 p-5 rounded-2xl">
          <ReadinessItem label="Loading Intelligence Engine..." isReady={step >= 1} />
          <ReadinessItem label="Checking Data Analysis Models..." isReady={step >= 2} />
          <ReadinessItem label="Tuning Forecast Engine..." isReady={step >= 3} />
          <ReadinessItem label="Compiling Executive Reporting..." isReady={step >= 4} />
        </div>

        {/* Bottom Loading Text */}
        <div className="text-[10px] text-slate-500 uppercase tracking-widest font-mono pt-4">
          {step < 5 ? (
            <div className="flex items-center justify-center gap-2">
              <span className="w-2 h-2 border border-slate-500 border-t-blue-500 rounded-full animate-spin" />
              Initializing modules...
            </div>
          ) : (
            <span className="text-emerald-500 font-bold">Launch Intelligence Engine</span>
          )}
        </div>
      </div>
    </div>
  )
}

function ReadinessItem({ label, isReady }: { label: string; isReady: boolean }) {
  return (
    <div className="flex items-center justify-between text-xs py-0.5">
      <span className={isReady ? 'text-slate-350 font-semibold' : 'text-slate-500'}>
        {isReady ? label.replace('Loading ', '').replace('Checking ', '').replace('Tuning ', '').replace('Compiling ', '').replace('...', '') + ' Ready' : label}
      </span>
      {isReady ? (
        <span className="text-emerald-500 font-bold text-sm">✓</span>
      ) : (
        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
      )}
    </div>
  )
}
