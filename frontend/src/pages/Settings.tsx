import { useState } from 'react'
import { User, Bell, Sparkles, Download, LayoutGrid, CheckCircle, Save, Building, Clock } from 'lucide-react'
import { useAuth } from '../lib/auth'

export default function SettingsPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<'profile' | 'workspace' | 'ai' | 'notifications' | 'export'>('profile')

  const [saved, setSaved] = useState(false)

  // Profile State
  const [profile, setProfile] = useState({
    name: localStorage.getItem('user_name') || '',
    email: localStorage.getItem('user_email') || user?.email || '',
    role: localStorage.getItem('user_role') || '',
    org: localStorage.getItem('user_org') || ''
  })

  // Workspace State
  const [workspace, setWorkspace] = useState({
    name: localStorage.getItem('workspace_name') || 'Main Analytics Hub',
    theme: localStorage.getItem('theme') || 'light',
    timezone: 'UTC-05:00 Eastern Time',
    language: 'en-US'
  })

  // AI Analyst State
  const [aiSettings, setAiSettings] = useState({
    personality: 'Executive Summaries',
    model: 'Deep Analysis (Standard)',
    maxTokens: '2048'
  })

  // Notifications State
  const [notifications, setNotifications] = useState({
    reportEmail: true,
    anomalyAlerts: true,
    weeklySummaries: false
  })

  // Export Settings State
  const [exportPrefs, setExportPrefs] = useState({
    pdfStyle: 'Corporate Navy',
    widescreenPPT: true,
    includeAppendix: true
  })

  const handleSave = () => {
    localStorage.setItem('user_name', profile.name)
    localStorage.setItem('user_email', profile.email)
    localStorage.setItem('user_role', profile.role)
    localStorage.setItem('user_org', profile.org)
    localStorage.setItem('workspace_name', workspace.name)
    localStorage.setItem('theme', workspace.theme)
    localStorage.setItem('language', workspace.language)
    localStorage.setItem('timezone', workspace.timezone)
    
    // Apply theme changes to document element
    if (workspace.theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }

    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="animate-fade-in max-w-5xl mx-auto space-y-8">
      {/* Page Header */}
      <div className="page-header pb-4 border-b border-slate-200 dark:border-slate-800">
        <h1 className="page-title text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <LayoutGrid className="text-blue-600" size={24} />
          Settings & Preferences
        </h1>
        <p className="page-subtitle text-sm text-slate-500 dark:text-slate-400 mt-1">
          Customize your profile, workspace settings, AI analyst, and export styling.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        <div className="flex flex-row md:flex-col gap-1.5 overflow-x-auto pb-2 md:pb-0 md:col-span-1 whitespace-nowrap scrollbar-none">
          <button
            onClick={() => setActiveTab('profile')}
            className={`flex items-center gap-2.5 px-4 py-3 text-sm font-semibold rounded-xl transition-all ${
              activeTab === 'profile'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <User size={18} />
            Profile & Account
          </button>
          
          <button
            onClick={() => setActiveTab('workspace')}
            className={`flex items-center gap-2.5 px-4 py-3 text-sm font-semibold rounded-xl transition-all ${
              activeTab === 'workspace'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <Building size={18} />
            Workspace & UI
          </button>

          <button
            onClick={() => setActiveTab('ai')}
            className={`flex items-center gap-2.5 px-4 py-3 text-sm font-semibold rounded-xl transition-all ${
              activeTab === 'ai'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <Sparkles size={18} />
            AI Analyst Options
          </button>

          <button
            onClick={() => setActiveTab('notifications')}
            className={`flex items-center gap-2.5 px-4 py-3 text-sm font-semibold rounded-xl transition-all ${
              activeTab === 'notifications'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <Bell size={18} />
            Notifications
          </button>

          <button
            onClick={() => setActiveTab('export')}
            className={`flex items-center gap-2.5 px-4 py-3 text-sm font-semibold rounded-xl transition-all ${
              activeTab === 'export'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <Download size={18} />
            Export Settings
          </button>
        </div>

        {/* Configuration Panel */}
        <div className="md:col-span-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm p-6 space-y-6">
          
          {/* PROFILE TAB */}
          {activeTab === 'profile' && (
            <div className="space-y-4 animate-fade-in">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <User className="text-blue-600" size={20} />
                Profile & Corporate Account
              </h3>
              <p className="text-xs text-slate-500">Configure your user account credentials and enterprise title.</p>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">Full Name</label>
                  <input
                    type="text"
                    value={profile.name}
                    onChange={e => setProfile({ ...profile, name: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
                    placeholder="Enter your name"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">Email Address</label>
                  <input
                    type="email"
                    value={profile.email}
                    onChange={e => setProfile({ ...profile, email: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
                    placeholder="Enter your email"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">Corporate Role</label>
                  <input
                    type="text"
                    value={profile.role}
                    onChange={e => setProfile({ ...profile, role: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
                    placeholder="Enter your role"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">Organization Name</label>
                  <input
                    type="text"
                    value={profile.org}
                    onChange={e => setProfile({ ...profile, org: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
                    placeholder="Enter organization name"
                  />
                </div>
              </div>

              {/* Activity History Card */}
              <div className="border-t border-slate-150 dark:border-slate-800 pt-6 mt-6">
                <h4 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-1">
                  <Clock className="text-blue-600" size={18} />
                  Recent Activity & Data History
                </h4>
                <p className="text-xs text-slate-500 mb-4">View your recent file uploads, analysis executions, and report compilations.</p>
                <div className="overflow-x-auto w-full rounded-xl border border-slate-150 dark:border-slate-800">
                  <table className="w-full text-left text-xs border-collapse min-w-[500px]">
                    <thead>
                      <tr className="bg-slate-50 dark:bg-slate-950/40 border-b border-slate-150 dark:border-slate-800 text-slate-600 dark:text-slate-400 font-bold uppercase tracking-wider">
                        <th className="p-3">Event / Action</th>
                        <th className="p-3">Target Asset</th>
                        <th className="p-3">Status</th>
                        <th className="p-3">Timestamp</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-350">
                      {[
                        { event: 'PowerPoint Export', asset: 'sample_sales.csv', status: 'Success', time: '10 mins ago', color: 'bg-emerald-500/10 text-emerald-600' },
                        { event: 'PDF Report Generation', asset: 'sample_sales.csv', status: 'Success', time: '14 mins ago', color: 'bg-emerald-500/10 text-emerald-600' },
                        { event: 'Dataset Upload', asset: 'sample_sales.csv (24.5 KB)', status: 'Success', time: '22 mins ago', color: 'bg-emerald-500/10 text-emerald-600' },
                        { event: 'AI Forecast Run', asset: 'sample_sales.csv [Revenue]', status: 'Success', time: '40 mins ago', color: 'bg-emerald-500/10 text-emerald-600' },
                      ].map((act, i) => (
                        <tr key={i} className="hover:bg-slate-50/40 dark:hover:bg-slate-800/10 transition-colors">
                          <td className="p-3 font-semibold text-slate-900 dark:text-white">{act.event}</td>
                          <td className="p-3 font-mono text-[10px] text-slate-500 dark:text-slate-400">{act.asset}</td>
                          <td className="p-3">
                            <span className={`px-2 py-0.5 rounded-full font-bold text-[9px] ${act.color}`}>
                              {act.status}
                            </span>
                          </td>
                          <td className="p-3 text-slate-400">{act.time}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          )}

          {/* WORKSPACE & UI TAB */}
          {activeTab === 'workspace' && (
            <div className="space-y-4 animate-fade-in">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Building className="text-blue-600" size={20} />
                Workspace Settings
              </h3>
              <p className="text-xs text-slate-500">Configure theme, language preferences, and default workspace names.</p>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">Workspace Hub Name</label>
                  <input
                    type="text"
                    value={workspace.name}
                    onChange={e => setWorkspace({ ...workspace, name: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">Theme Mode</label>
                  <select
                    value={workspace.theme}
                    onChange={e => setWorkspace({ ...workspace, theme: e.target.value })}
                    className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
                  >
                    <option value="light">Light Mode (Fluent Classic)</option>
                    <option value="dark">Dark Mode (Premium Executive)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">Time Zone</label>
                  <select
                    value={workspace.timezone}
                    onChange={e => setWorkspace({ ...workspace, timezone: e.target.value })}
                    className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
                  >
                    <option value="UTC-05:00 Eastern Time">UTC-05:00 Eastern Time</option>
                    <option value="UTC+00:00 GMT">UTC+00:00 GMT</option>
                    <option value="UTC+05:30 India Time">UTC+05:30 India Time</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">Language Format</label>
                  <select
                    value={workspace.language}
                    onChange={e => setWorkspace({ ...workspace, language: e.target.value })}
                    className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
                  >
                    <option value="en-US">English (United States) - Millions/Billions</option>
                    <option value="en-IN">English (India) - Lakhs/Crores</option>
                    <option value="en-GB">English (United Kingdom)</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* AI ANALYST TAB */}
          {activeTab === 'ai' && (
            <div className="space-y-4 animate-fade-in">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Sparkles className="text-purple-600" size={20} />
                AI Analyst Configurations
              </h3>
              <p className="text-xs text-slate-500">Fine-tune recommendations detail level and context reasoning options.</p>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">Analyst Personality</label>
                  <select
                    value={aiSettings.personality}
                    onChange={e => setAiSettings({ ...aiSettings, personality: e.target.value })}
                    className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
                  >
                    <option value="Executive Summaries">Executive Summaries (High Level)</option>
                    <option value="Balanced Insights">Balanced Insights (Standard)</option>
                    <option value="Technical/Detailed">Detailed Data Mining (Heavy Technical)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">Reasoning Engine Model</label>
                  <select
                    value={aiSettings.model}
                    onChange={e => setAiSettings({ ...aiSettings, model: e.target.value })}
                    className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
                  >
                    <option value="Deep Analysis (Standard)">Deep Analysis (Standard)</option>
                    <option value="Ultra Precision (Advanced)">Ultra Precision (Advanced)</option>
                  </select>
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">Context Window Limit</label>
                  <input
                    type="range"
                    min="1024"
                    max="8192"
                    step="1024"
                    value={aiSettings.maxTokens}
                    onChange={e => setAiSettings({ ...aiSettings, maxTokens: e.target.value })}
                    className="w-full"
                  />
                  <div className="text-right text-xs text-slate-500 font-mono mt-1">{aiSettings.maxTokens} Context Tokens</div>
                </div>
              </div>
            </div>
          )}

          {/* NOTIFICATIONS TAB */}
          {activeTab === 'notifications' && (
            <div className="space-y-4 animate-fade-in">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Bell className="text-orange-500" size={20} />
                Notification Channels
              </h3>
              <p className="text-xs text-slate-500">Enable notification rules to alert you on anomalies and reports compilations.</p>
              
              <div className="space-y-3 pt-2">
                <label className="flex items-center gap-3 p-3 border border-slate-100 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-all cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.reportEmail}
                    onChange={e => setNotifications({ ...notifications, reportEmail: e.target.checked })}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <div>
                    <div className="text-sm font-semibold text-slate-800 dark:text-white">Email compiled reports</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">Receive a copy of generated PDF and PPTX decks directly in your inbox.</div>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-3 border border-slate-100 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-all cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.anomalyAlerts}
                    onChange={e => setNotifications({ ...notifications, anomalyAlerts: e.target.checked })}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <div>
                    <div className="text-sm font-semibold text-slate-800 dark:text-white">Immediate anomaly alerts</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">Alert on primary channel if consensus tests detect critical outliers in sales or volumes.</div>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-3 border border-slate-100 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-all cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.weeklySummaries}
                    onChange={e => setNotifications({ ...notifications, weeklySummaries: e.target.checked })}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <div>
                    <div className="text-sm font-semibold text-slate-800 dark:text-white">Weekly health reviews</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">Get a weekend roll-up of composite business scores and top category drivers.</div>
                  </div>
                </label>
              </div>
            </div>
          )}

          {/* EXPORT SETTINGS TAB */}
          {activeTab === 'export' && (
            <div className="space-y-4 animate-fade-in">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Download className="text-green-600" size={20} />
                Export Styling Configurations
              </h3>
              <p className="text-xs text-slate-500">Customize default cover layouts, margins, and report details.</p>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">PDF Theme Design</label>
                  <select
                    value={exportPrefs.pdfStyle}
                    onChange={e => setExportPrefs({ ...exportPrefs, pdfStyle: e.target.value })}
                    className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
                  >
                    <option value="Corporate Navy">Corporate Navy (McKinsey Style)</option>
                    <option value="Minimalist Slate">Minimalist Slate (Modern Tech)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">PowerPoint Aspect Ratio</label>
                  <select
                    value={exportPrefs.widescreenPPT ? '16:9' : '4:3'}
                    onChange={e => setExportPrefs({ ...exportPrefs, widescreenPPT: e.target.value === '16:9' })}
                    className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
                  >
                    <option value="16:9">Widescreen Presentation (16:9)</option>
                    <option value="4:3">Standard Slide Deck (4:3)</option>
                  </select>
                </div>
                <div className="sm:col-span-2">
                  <label className="flex items-center gap-3 p-3 border border-slate-100 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-all cursor-pointer">
                    <input
                      type="checkbox"
                      checked={exportPrefs.includeAppendix}
                      onChange={e => setExportPrefs({ ...exportPrefs, includeAppendix: e.target.checked })}
                      className="rounded text-blue-600 focus:ring-blue-500"
                    />
                    <div>
                      <div className="text-sm font-semibold text-slate-800 dark:text-white">Include schema profiling appendix</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">Append row/column metadata counts, types, and validation details to final outputs.</div>
                    </div>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Action Row */}
          {['profile', 'workspace', 'ai', 'notifications', 'export'].includes(activeTab) && (
            <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
              <div>
                {saved && (
                  <span className="flex items-center gap-1.5 text-sm text-green-600 font-semibold animate-fade-in">
                    <CheckCircle size={16} />
                    Settings saved successfully!
                  </span>
                )}
              </div>
              <button
                onClick={handleSave}
                className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors shadow-sm cursor-pointer"
              >
                <Save size={16} />
                Save Preferences
              </button>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}

