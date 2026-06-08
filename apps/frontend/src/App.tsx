/**
 * InsightIQ — Main Application Shell
 *
 * Layout: Fixed sidebar + main content area with page routing.
 */

import { useState } from 'react'
import { Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import {
  Home, Upload, BarChart3, AlertTriangle, TrendingUp,
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
import Login from './pages/Login'
import { useAuth } from './lib/auth'
import type { SafeAny } from './types'

const NAV_ITEMS = [
  { path: '/', icon: Home, label: 'Home' },
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
  { path: '/settings', icon: Settings, label: 'Settings' },
]

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [datasetId, setDatasetId] = useState<string | null>(null)
  const [datasetName, setDatasetName] = useState<string>('')
  const [datasetMeta, setDatasetMeta] = useState<SafeAny>(null)
  const navigate = useNavigate()
  
  const { user, isLoading, logout } = useAuth()

  const handleDatasetLoaded = (id: string, name: string, meta: SafeAny) => {
    setDatasetId(id)
    setDatasetName(name)
    setDatasetMeta(meta)
    navigate('/')
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

  if (!user) {
    return <Login onSuccess={() => navigate('/')} />
  }

  return (
    <div className="flex min-h-screen" style={{ background: 'var(--color-bg)' }}>
      {/* ── Sidebar ────────────────────────────────────────────────── */}
      <aside
        className={`sidebar transition-transform duration-300 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand */}
        <div className="sidebar-brand">
          <div className="flex items-center gap-2.5">
            <img src="/logo.png" alt="InsightIQ Logo" className="w-9 h-9 object-contain rounded-xl" />
            <div>
              <div className="font-extrabold text-base tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
                InsightIQ
              </div>
              <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                AI Data Intelligence
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
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

        {/* User Profile and Logout */}
        <div className="p-4 border-t flex items-center justify-between bg-slate-50/50" style={{ borderColor: 'var(--color-border-light)' }}>
          <div className="min-w-0">
            <div className="text-xs font-semibold text-slate-700 truncate" title={user.email}>
              {user.email}
            </div>
            <div className="text-[10px] text-slate-400 capitalize">
              Role: {user.role}
            </div>
          </div>
          <button
            onClick={logout}
            className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors cursor-pointer"
            title="Sign Out"
          >
            <LogOut size={16} />
          </button>
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
        </Routes>
      </main>
    </div>
  )
}
