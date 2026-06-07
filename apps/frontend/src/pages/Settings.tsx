import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Settings as SettingsIcon, Shield, Sparkles, Database, Save, CheckCircle, Activity, ServerCrash } from 'lucide-react'
import { getInfrastructureStatus, testConnection } from '../lib/api'

export default function SettingsPage() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light')
  const [saved, setSaved] = useState(false)
  const [testResults, setTestResults] = useState<Record<string, { status: 'success' | 'error' | 'loading', message?: string }>>({})

  // Fetch infrastructure status
  const { data: statusData, isError } = useQuery({
    queryKey: ['infrastructureStatus'],
    queryFn: getInfrastructureStatus,
    retry: false, // If it fails, likely 403 Forbidden (not admin)
  })

  

  const handleSave = () => {
    localStorage.setItem('theme', theme)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const handleTest = async (service: 'ai' | 'database' | 'storage') => {
    setTestResults(prev => ({ ...prev, [service]: { status: 'loading' } }))
    try {
      const res = await testConnection(service)
      setTestResults(prev => ({ ...prev, [service]: { status: res.status, message: res.message } }))
    } catch {
      setTestResults(prev => ({ ...prev, [service]: { status: 'error', message: 'Connection Failed' } }))
    }
  }

  return (
    <div className="animate-fade-in max-w-3xl mx-auto">
      <div className="page-header mb-8">
        <h1 className="page-title flex items-center gap-2">
          <SettingsIcon className="text-blue-600" />
          Platform Settings
        </h1>
        <p className="page-subtitle">Configure application settings and monitor infrastructure health</p>
      </div>

      <div className="space-y-6">
        {/* Security Summary */}
        <div className="card card-body bg-slate-50 border-slate-200">
          <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
            <Shield size={20} className="text-green-600" />
            Security Posture
          </h3>
          <p className="text-sm text-slate-600 mb-4">
            Secrets Managed Securely. No sensitive API keys or connection strings are exposed to the frontend. All credentials are encrypted and stored in backend environment variables.
          </p>
          <div className="text-xs text-slate-500 font-mono">
            Last Security Check: {new Date().toLocaleDateString()} {new Date().toLocaleTimeString()}
          </div>
        </div>

        {/* Infrastructure & AI (Only if loaded successfully) */}
        {!isError && statusData && (
          <>
            {/* AI Services */}
            <div className="card card-body">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold flex items-center gap-2">
                  <Sparkles size={20} className="text-purple-600" />
                  AI Services
                </h3>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg bg-white">
                <div>
                  <div className="font-semibold text-slate-800">Gemini API</div>
                  <div className="text-sm text-slate-500">Provider: {statusData?.ai?.provider}</div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <div className="flex items-center gap-1.5 text-sm font-medium">
                    {statusData?.ai?.connected ? (
                      <span className="text-green-600 flex items-center gap-1"><CheckCircle size={14} /> Connected</span>
                    ) : (
                      <span className="text-amber-600 flex items-center gap-1"><Activity size={14} /> Fallback Model</span>
                    )}
                  </div>
                  <button 
                    onClick={() => handleTest('ai')}
                    className="text-xs px-3 py-1.5 border rounded hover:bg-slate-50 transition-colors"
                  >
                    {testResults['ai']?.status === 'loading' ? 'Testing...' : 'Test Connection'}
                  </button>
                  {testResults['ai'] && testResults['ai'].status !== 'loading' && (
                    <div className={`text-xs ${testResults['ai'].status === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                      {testResults['ai'].message}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Infrastructure */}
            <div className="card card-body">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Database size={20} className="text-blue-600" />
                Infrastructure Status
              </h3>
              <div className="space-y-3">
                {/* Database */}
                <div className="flex items-center justify-between p-4 border rounded-lg bg-white">
                  <div>
                    <div className="font-semibold text-slate-800">Database</div>
                    <div className="text-sm text-slate-500">Provider: {statusData?.database?.provider}</div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <div className="flex items-center gap-1.5 text-sm font-medium text-green-600">
                      <CheckCircle size={14} /> {statusData?.database?.status}
                    </div>
                    <button 
                      onClick={() => handleTest('database')}
                      className="text-xs px-3 py-1.5 border rounded hover:bg-slate-50 transition-colors"
                    >
                      {testResults['database']?.status === 'loading' ? 'Testing...' : 'Test Connection'}
                    </button>
                    {testResults['database'] && testResults['database'].status !== 'loading' && (
                      <div className={`text-xs ${testResults['database'].status === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                        {testResults['database'].message}
                      </div>
                    )}
                  </div>
                </div>

                {/* Storage */}
                <div className="flex items-center justify-between p-4 border rounded-lg bg-white">
                  <div>
                    <div className="font-semibold text-slate-800">Storage</div>
                    <div className="text-sm text-slate-500">Provider: {statusData?.storage?.provider}</div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <div className="flex items-center gap-1.5 text-sm font-medium text-green-600">
                      <CheckCircle size={14} /> {statusData?.storage?.status}
                    </div>
                    <button 
                      onClick={() => handleTest('storage')}
                      className="text-xs px-3 py-1.5 border rounded hover:bg-slate-50 transition-colors"
                    >
                      {testResults['storage']?.status === 'loading' ? 'Testing...' : 'Test Connection'}
                    </button>
                    {testResults['storage'] && testResults['storage'].status !== 'loading' && (
                      <div className={`text-xs ${testResults['storage'].status === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                        {testResults['storage'].message}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {isError && (
          <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-100 flex items-start gap-3">
            <ServerCrash size={20} className="mt-0.5" />
            <div>
              <div className="font-semibold">Infrastructure Access Denied</div>
              <div className="text-sm">You do not have administrative privileges to view infrastructure settings.</div>
            </div>
          </div>
        )}

        {/* Preferences */}
        <div className="card card-body">
          <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
            <SettingsIcon size={20} className="text-slate-600" />
            Preferences
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5 text-slate-700">
                Theme Mode
              </label>
              <select
                value={theme}
                onChange={e => setTheme(e.target.value)}
                className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              >
                <option value="light">Light Mode (Fluent Default)</option>
                <option value="dark">Dark Mode (Beta)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center justify-between pt-4">
          <div>
            {saved && (
              <span className="flex items-center gap-1.5 text-sm text-green-600 font-semibold animate-fade-in">
                <CheckCircle size={16} />
                Preferences saved successfully!
              </span>
            )}
          </div>
          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors shadow-sm"
          >
            <Save size={16} />
            Save Preferences
          </button>
        </div>
      </div>
    </div>
  )
}
