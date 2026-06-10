/**
 * InsightIQ — Upload Page
 *
 * Drag-and-drop file upload with progress, schema preview, and domain detection.
 * Followed by business context definition and AI analysis strategy formulation.
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { Upload as UploadIcon, FileSpreadsheet, CheckCircle, AlertCircle, Loader2, X, Database, ArrowRight, Trash2, Sparkles } from 'lucide-react'
import { uploadDataset, listDatasets, deleteDataset, updateDatasetContext, ApiError } from '../lib/api'
import { useAuth } from '../lib/auth'
import type { SafeAny } from '../types'

interface UploadProps {
  onDatasetLoaded: (id: string, name: string, meta: Record<string, unknown>) => void
}

export default function UploadPage({ onDatasetLoaded }: UploadProps) {
  const { user } = useAuth()
  // Navigation & View Modes
  const [viewMode, setViewMode] = useState<'upload' | 'capture' | 'strategy'>('upload')
  const [activeDatasetId, setActiveDatasetId] = useState<string | null>(null)
  const [activeDatasetName, setActiveDatasetName] = useState<string>('')
  const [activeDatasetMeta, setActiveDatasetMeta] = useState<Record<string, unknown>>({})

  // File Upload State
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [diagnostics, setDiagnostics] = useState<Record<string, SafeAny> | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [datasets, setDatasets] = useState<Record<string, SafeAny>[]>([])

  // Context Capture Form States
  const [businessProblem, setBusinessProblem] = useState('')
  const [analysisGoal, setAnalysisGoal] = useState('Revenue Growth')
  const [successMetric, setSuccessMetric] = useState('Revenue')

  // Strategy Checklist State
  const [strategyRunning, setStrategyRunning] = useState(false)
  const [checkedSteps, setCheckedSteps] = useState<number>(0)
  const [contextSaving, setContextSaving] = useState(false)

  const fetchDatasets = useCallback(async () => {
    try {
      const list = await listDatasets()
      setDatasets(list)
    } catch (err) {
      console.error('Failed to list datasets:', err)
    }
  }, [user])

  useEffect(() => {
    fetchDatasets()
  }, [fetchDatasets])

  // Strategy Checklist Tick Animation
  useEffect(() => {
    if (viewMode !== 'strategy') return
    setStrategyRunning(true)
    setCheckedSteps(0)
    
    const interval = setInterval(() => {
      setCheckedSteps(prev => {
        if (prev >= 6) {
          clearInterval(interval)
          setStrategyRunning(false)
          return 6
        }
        return prev + 1
      })
    }, 600)

    return () => clearInterval(interval)
  }, [viewMode])

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (!window.confirm('Are you sure you want to delete this dataset?')) return
    try {
      await deleteDataset(id)
      fetchDatasets()
    } catch (err) {
      console.error('Failed to delete dataset:', err)
      alert('Failed to delete dataset')
    }
  }

  const handleSelectDataset = (ds: SafeAny) => {
    setActiveDatasetId(ds.id || ds.dataset_id)
    setActiveDatasetName(ds.name)
    setActiveDatasetMeta({
      rows: ds.rows,
      columns: ds.columns,
    })
    setViewMode('capture')
  }

  const handleFile = useCallback(async (file: File) => {
    setError(null)
    setResult(null)
    setDiagnostics(null)
    setUploading(true)
    setProgress(10)

    try {
      const progressTimer = setInterval(() => {
        setProgress(p => Math.min(p + 15, 85))
      }, 400)

      const data = await uploadDataset(file)

      clearInterval(progressTimer)
      setProgress(100)
      setResult(data)
      setDiagnostics(data.diagnostics || null)

      // Auto-navigate to problem capture after a short delay
      setTimeout(() => {
        setActiveDatasetId(data.dataset_id)
        setActiveDatasetName(data.name)
        setActiveDatasetMeta({
          rows: data.rows,
          columns: data.columns,
        })
        setViewMode('capture')
      }, 3000)
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(err.message)
        setDiagnostics(err.diagnostics || null)
      } else {
        setError(err instanceof Error ? err.message : 'Upload failed')
        setDiagnostics(null)
      }
    } finally {
      setUploading(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [handleFile])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const presets = [
    {
      label: 'Reduce Customer Churn',
      problem: 'Analyze repeat purchase rates and RFM cohorts to identify customer segments with highest churn risk and decline in loyalty.',
      goal: 'Customer Intelligence',
      metric: 'Churn Rate',
    },
    {
      label: 'Grow Sales Revenue',
      problem: 'Audit temporal sales trends, top product contributions, and high-value orders to identify key pricing and growth opportunities.',
      goal: 'Revenue Growth',
      metric: 'Revenue',
    },
    {
      label: 'Optimize Marketing Spend',
      problem: 'Examine campaigns and promotional conversion patterns to optimize return on marketing investments and traffic cost efficiency.',
      goal: 'Marketing Analytics',
      metric: 'ROAS',
    },
    {
      label: 'Enhance Operations',
      problem: 'Diagnose processing anomalies, bottlenecks, and inventory safety stock limits to reduce average transaction cycle time.',
      goal: 'Operational Efficiency',
      metric: 'Cycle Time',
    }
  ]

  const applyPreset = (preset: typeof presets[0]) => {
    setBusinessProblem(preset.problem)
    setAnalysisGoal(preset.goal)
    setSuccessMetric(preset.metric)
  }

  const strategySteps = [
    'Scan dataset headers and columns to detect data schema semantics.',
    `Filter and align KPIs with target success metric: "${successMetric}".`,
    `Prioritize RFM concentration profiles matching the goal: "${analysisGoal}".`,
    'Apply 3-sigma and IQR models to isolate transaction anomalies.',
    'Formulate 90-day scenarios (expected growth vectors vs downside limits).',
    'Structure 30-60-90 day implementation roadmap recommendations.'
  ]

  // Render different sub-screens based on viewMode
  if (viewMode === 'capture') {
    return (
      <div className="animate-fade-in max-w-2xl mx-auto py-6">
        <div className="page-header text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full mb-3"
               style={{ background: 'var(--color-primary-50)', color: 'var(--color-primary)' }}>
            <Sparkles size={14} />
            <span className="text-[10px] font-bold uppercase tracking-wider">Step 2: Define Context</span>
          </div>
          <h1 className="page-title text-2xl font-extrabold" style={{ color: 'var(--color-text-primary)' }}>Define Business Objective</h1>
          <p className="page-subtitle text-sm" style={{ color: 'var(--color-text-secondary)' }}>
            Tailor the analytical models and AI strategy to your specific business problem
          </p>
        </div>

        <div className="card card-body space-y-6 shadow-xl border" style={{ borderColor: 'var(--color-border)', borderRadius: '16px', background: 'var(--color-surface)' }}>
          <div>
            <label className="block text-sm font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>
              What business problem are you trying to solve?
            </label>
            <textarea
              className="w-full p-3 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={{ 
                background: 'var(--color-surface)', 
                borderColor: 'var(--color-border)', 
                color: 'var(--color-text-primary)',
                minHeight: '100px'
              }}
              placeholder="E.g., We want to understand customer loyalty factors and reduce retention leakage..."
              value={businessProblem}
              onChange={(e) => setBusinessProblem(e.target.value)}
            />
            <div className="mt-3">
              <span className="text-xs font-semibold" style={{ color: 'var(--color-text-muted)' }}>Quick Presets:</span>
              <div className="flex flex-wrap gap-2 mt-1.5">
                {presets.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => applyPreset(p)}
                    className="text-xs px-3 py-1.5 rounded-full border transition-all hover:bg-slate-100 font-medium"
                    style={{ 
                      background: 'var(--color-surface)', 
                      borderColor: 'var(--color-border)',
                      color: 'var(--color-text-secondary)'
                    }}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>
                Analysis Goal
              </label>
              <select
                className="w-full p-3 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                style={{ 
                  background: 'var(--color-surface)', 
                  borderColor: 'var(--color-border)',
                  color: 'var(--color-text-primary)'
                }}
                value={analysisGoal}
                onChange={(e) => setAnalysisGoal(e.target.value)}
              >
                <option>Revenue Growth</option>
                <option>Customer Intelligence</option>
                <option>Marketing Analytics</option>
                <option>Operational Efficiency</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>
                Primary Success Metric
              </label>
              <input
                type="text"
                className="w-full p-3 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                style={{ 
                  background: 'var(--color-surface)', 
                  borderColor: 'var(--color-border)',
                  color: 'var(--color-text-primary)'
                }}
                placeholder="E.g., Churn Rate, MRR, ROAS"
                value={successMetric}
                onChange={(e) => setSuccessMetric(e.target.value)}
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t" style={{ borderColor: 'var(--color-border-light)' }}>
            <button
              onClick={() => setViewMode('upload')}
              className="btn btn-secondary text-sm px-4 py-2"
            >
              Back to Upload
            </button>
            <button
              onClick={() => {
                if (!businessProblem.trim()) {
                  alert('Please enter a business problem statement or select a quick preset.');
                  return;
                }
                setViewMode('strategy');
              }}
              className="btn btn-primary text-sm px-5 py-2 flex items-center gap-1.5"
              disabled={!businessProblem.trim()}
            >
              Formulate Strategy <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (viewMode === 'strategy') {
    return (
      <div className="animate-fade-in max-w-2xl mx-auto py-6">
        <div className="page-header text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full mb-3"
               style={{ background: 'var(--color-primary-50)', color: 'var(--color-primary)' }}>
            <Sparkles size={14} />
            <span className="text-[10px] font-bold uppercase tracking-wider">Step 3: AI Analysis Strategy</span>
          </div>
          <h1 className="page-title text-2xl font-extrabold" style={{ color: 'var(--color-text-primary)' }}>AI Analysis Strategy Formulation</h1>
          <p className="page-subtitle text-sm" style={{ color: 'var(--color-text-secondary)' }}>
            InsightIQ is generating a targeted analytical plan based on your business objective
          </p>
        </div>

        <div className="card card-body space-y-6 shadow-xl border" style={{ borderColor: 'var(--color-border)', borderRadius: '16px', background: 'var(--color-surface)' }}>
          <div className="p-4 rounded-xl space-y-2.5 shadow-sm" style={{ background: 'var(--color-surface-hover)', border: '1px solid var(--color-border)' }}>
            <div className="flex justify-between items-center border-b pb-2" style={{ borderColor: 'var(--color-border-light)' }}>
              <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: 'var(--color-text-muted)' }}>Stated Business Problem</span>
              <span className="badge badge-info text-xs">{analysisGoal}</span>
            </div>
            <div className="text-sm font-semibold italic" style={{ color: 'var(--color-text-primary)' }}>
              "{businessProblem}"
            </div>
            <div className="text-xs font-bold flex items-center gap-1.5" style={{ color: 'var(--color-success)' }}>
              <CheckCircle size={14} /> Success Metric Focus: {successMetric}
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">AI Tactical Analysis Plan</h3>
            <div className="space-y-3">
              {strategySteps.map((step, idx) => {
                const isChecked = checkedSteps > idx;
                const isCurrent = checkedSteps === idx;
                return (
                  <div 
                    key={idx} 
                    className="flex items-start gap-3 p-3 rounded-lg border transition-all duration-300"
                    style={{ 
                      background: isChecked ? 'rgba(5, 150, 105, 0.02)' : isCurrent ? 'rgba(37, 99, 235, 0.02)' : 'var(--color-surface)',
                      borderColor: isChecked ? 'rgba(5, 150, 105, 0.15)' : isCurrent ? 'rgba(37, 99, 235, 0.2)' : 'var(--color-border)',
                      opacity: isChecked || isCurrent ? 1 : 0.5
                    }}
                  >
                    <div className="mt-0.5 flex-shrink-0">
                      {isChecked ? (
                        <CheckCircle size={18} className="text-emerald-600 animate-scale-in" />
                      ) : isCurrent ? (
                        <Loader2 size={18} className="text-blue-600 animate-spin" />
                      ) : (
                        <div className="w-[18px] h-[18px] rounded-full border border-slate-300" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div 
                        className="text-sm font-medium" 
                        style={{ 
                          color: isChecked ? 'var(--color-success)' : isCurrent ? 'var(--color-primary)' : 'var(--color-text-secondary)'
                        }}
                      >
                        {step}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t" style={{ borderColor: 'var(--color-border-light)' }}>
            <button
              onClick={() => setViewMode('capture')}
              className="btn btn-secondary text-sm px-4 py-2"
              disabled={contextSaving || strategyRunning}
            >
              Change Objective
            </button>
            <button
              onClick={async () => {
                if (!activeDatasetId) return;
                setContextSaving(true);
                try {
                  await updateDatasetContext(activeDatasetId, {
                    business_problem: businessProblem,
                    analysis_goal: analysisGoal,
                    success_metric: successMetric
                  });
                  onDatasetLoaded(activeDatasetId, activeDatasetName, activeDatasetMeta);
                } catch (err) {
                  console.error('Failed to save context:', err);
                  alert('Failed to register analysis objective. Transitioning to dashboard.');
                  onDatasetLoaded(activeDatasetId, activeDatasetName, activeDatasetMeta);
                } finally {
                  setContextSaving(false);
                }
              }}
              className="btn btn-primary text-sm px-5 py-2 flex items-center gap-1.5"
              disabled={strategyRunning || contextSaving}
            >
              {contextSaving ? (
                <>
                  <Loader2 size={16} className="animate-spin" /> Ingesting Analytics...
                </>
              ) : (
                <>
                  Launch Context-Driven Dashboard <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="animate-fade-in max-w-3xl mx-auto">
      <div className="page-header">
        <h1 className="page-title">Upload Data</h1>
        <p className="page-subtitle">
          Drop your dataset and InsightIQ will automatically analyze it
        </p>
      </div>

      {/* Drop Zone */}
      <div
        className="card cursor-pointer transition-all p-8 sm:p-16 text-center"
        style={{
          border: isDragging ? '2px dashed var(--color-primary)' : '2px dashed var(--color-border)',
          background: isDragging ? 'var(--color-primary-50)' : 'var(--color-surface)',
        }}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={() => setIsDragging(false)}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls,.parquet,.json,.tsv"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />

        {uploading ? (
          <div>
            <Loader2 size={48} className="mx-auto mb-4 animate-spin" style={{ color: 'var(--color-primary)' }} />
            <div className="font-semibold text-lg mb-2" style={{ color: 'var(--color-text-primary)' }}>
              Analyzing your data...
            </div>
            <div className="w-full max-w-xs mx-auto h-2 rounded-full overflow-hidden"
                 style={{ background: 'var(--color-border-light)' }}>
              <div
                className="h-full rounded-full transition-all duration-300"
                style={{ width: `${progress}%`, background: 'var(--color-primary)' }}
              />
            </div>
            <div className="text-sm mt-2" style={{ color: 'var(--color-text-muted)' }}>
              {progress < 30 ? 'Reading file...' :
               progress < 60 ? 'Detecting schema & domain...' :
               progress < 85 ? 'Computing KPIs & quality...' :
               'Finalizing analysis...'}
            </div>
          </div>
        ) : result ? (
          <SuccessView result={result} />
        ) : (
          <div>
            <div className="w-20 h-20 mx-auto mb-5 rounded-2xl flex items-center justify-center"
                 style={{ background: 'var(--color-primary-50)' }}>
              <UploadIcon size={36} style={{ color: 'var(--color-primary)' }} />
            </div>
            <div className="font-semibold text-lg mb-1" style={{ color: 'var(--color-text-primary)' }}>
              {isDragging ? 'Drop your file here' : 'Drag & drop your dataset'}
            </div>
            <div className="text-sm mb-4" style={{ color: 'var(--color-text-secondary)' }}>
              or click to browse files
            </div>
            <div className="flex flex-wrap justify-center gap-2">
              {['CSV', 'Excel', 'Parquet', 'JSON', 'TSV'].map(fmt => (
                <span key={fmt} className="badge badge-info">{fmt}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="card card-body mt-4 flex items-center gap-3"
             style={{ background: 'var(--color-danger-light)', border: '1px solid var(--color-danger)' }}>
          <AlertCircle size={20} style={{ color: 'var(--color-danger)' }} />
          <div>
            <div className="font-semibold text-sm" style={{ color: 'var(--color-danger)' }}>Upload Failed</div>
            <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>{error}</div>
          </div>
          <button onClick={() => { setError(null); setDiagnostics(null); }} className="ml-auto" style={{ color: 'var(--color-text-muted)' }}>
            <X size={16} />
          </button>
        </div>
      )}

      {/* Diagnostics Debug Panel */}
      {diagnostics && (
        <div className="card mt-6 border transition-all animate-fade-in" style={{ borderColor: 'var(--color-border)', borderRadius: '12px', overflow: 'hidden' }}>
          <div className="card-header border-b" style={{ padding: '1rem 1.5rem', background: 'var(--color-surface-hover)' }}>
            <div className="font-semibold text-base flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
              <span className="w-2.5 h-2.5 rounded-full animate-pulse" style={{ background: diagnostics.failure_stage ? 'var(--color-danger)' : 'var(--color-success)' }} />
              Upload Diagnostics & Parser Debug
            </div>
          </div>
          <div className="card-body" style={{ padding: '1.5rem' }}>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: 'File Name', value: String(diagnostics.filename || 'unknown') },
                { label: 'Extension', value: String(diagnostics.extension || '').toUpperCase() },
                { label: 'Encoding', value: String(diagnostics.encoding || 'N/A') },
                { label: 'Parser Used', value: String(diagnostics.parser || 'unknown') },
                { label: 'Rows', value: diagnostics.rows !== undefined ? Number(diagnostics.rows).toLocaleString() : '0' },
                { label: 'Columns', value: diagnostics.columns !== undefined ? String(diagnostics.columns) : '0' },
                { label: 'Processing Time', value: `${diagnostics.processing_time_ms || 0} ms` },
                { 
                  label: 'Failure Stage', 
                  value: diagnostics.failure_stage 
                    ? <span className="font-semibold text-xs py-0.5 px-2 rounded-full" style={{ color: 'var(--color-danger)', background: 'var(--color-danger-light)' }}>{String(diagnostics.failure_stage).toUpperCase()}</span>
                    : <span className="font-semibold text-xs py-0.5 px-2 rounded-full" style={{ color: 'var(--color-success)', background: 'var(--color-success-light)' }}>SUCCESS</span>
                },
              ].map((item, index) => (
                <div key={index} className="flex flex-col p-3 rounded-lg border" style={{ background: 'var(--color-surface-hover)', borderColor: 'var(--color-border)' }}>
                  <span className="text-[10px] uppercase font-bold tracking-wider" style={{ color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>{item.label}</span>
                  <span className="text-sm font-semibold truncate" style={{ color: 'var(--color-text-primary)' }}>{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Recently Uploaded Datasets */}
      {datasets.length > 0 && (
        <div className="card mt-6 border animate-fade-in" style={{ borderColor: 'var(--color-border)', borderRadius: '12px', overflow: 'hidden' }}>
          <div className="card-header border-b" style={{ padding: '1rem 1.5rem', background: 'var(--color-surface-hover)' }}>
            <div className="font-semibold text-base flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
              <Database size={18} style={{ color: 'var(--color-primary)' }} />
              Recently Uploaded Datasets
            </div>
          </div>
          <div className="card-body" style={{ padding: '0' }}>
            <div className="divide-y" style={{ borderColor: 'var(--color-border)' }}>
              {datasets.map((ds) => (
                <div
                  key={ds.id}
                  onClick={() => handleSelectDataset(ds)}
                  className="flex items-center justify-between p-4 hover:bg-slate-50/50 cursor-pointer transition-colors"
                >
                  <div className="min-w-0 flex-1 pr-4">
                    <div className="font-semibold text-sm truncate" style={{ color: 'var(--color-text-primary)' }}>
                      {ds.name}
                    </div>
                    <div className="text-xs mt-0.5 flex items-center gap-2" style={{ color: 'var(--color-text-muted)' }}>
                      <span>Domain: <strong className="text-slate-700">{ds.domain || 'Unknown'}</strong></span>
                      <span>•</span>
                      <span>{Number(ds.rows || 0).toLocaleString()} rows</span>
                      <span>•</span>
                      <span>{ds.columns} cols</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <button
                      onClick={(e) => handleDelete(e, ds.id)}
                      className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                      title="Delete dataset"
                    >
                      <Trash2 size={16} />
                    </button>
                    <div className="p-2 text-slate-400 hover:text-blue-600 rounded-lg transition-all">
                      <ArrowRight size={16} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tips */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
        {[
          { icon: FileSpreadsheet, title: 'Any Format', desc: 'CSV, Excel, Parquet, JSON — we handle it all' },
          { icon: CheckCircle, title: 'Auto-Detection', desc: 'Schema, types, domain, and KPIs detected automatically' },
          { icon: UploadIcon, title: 'Up to 2GB', desc: 'Large datasets supported with intelligent sampling' },
        ].map((tip, i) => (
          <div key={i} className="card card-body flex items-start gap-3">
            <tip.icon size={20} style={{ color: 'var(--color-primary)', flexShrink: 0, marginTop: 2 }} />
            <div>
              <div className="font-semibold text-sm" style={{ color: 'var(--color-text-primary)' }}>{tip.title}</div>
              <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{tip.desc}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function SuccessView({ result }: { result: SafeAny }) {
  return (
    <div className="animate-scale-in">
      <CheckCircle size={48} className="mx-auto mb-4" style={{ color: 'var(--color-success)' }} />
      <div className="font-semibold text-lg mb-1" style={{ color: 'var(--color-text-primary)' }}>
        Analysis Complete!
      </div>
      <div className="text-sm mb-4" style={{ color: 'var(--color-text-secondary)' }}>
        Preparing business capture...
      </div>
      <div className="flex flex-wrap justify-center gap-3">
        <div className="badge badge-success">{Number(result.rows || 0).toLocaleString()} rows</div>
        <div className="badge badge-info">{result.columns} columns</div>
        <div className="badge badge-info">{result.domain?.name}</div>
        <div className="badge badge-success">Quality: {result.quality?.grade}</div>
      </div>
    </div>
  )
}
