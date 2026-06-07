/**
 * InsightIQ — Upload Page
 *
 * Drag-and-drop file upload with progress, schema preview, and domain detection.
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { Upload as UploadIcon, FileSpreadsheet, CheckCircle, AlertCircle, Loader2, X, Database, ArrowRight, Trash2 } from 'lucide-react'
import { uploadDataset, listDatasets, deleteDataset, ApiError } from '../lib/api'
import type { SafeAny } from '../types'

interface UploadProps {
  onDatasetLoaded: (id: string, name: string, meta: Record<string, unknown>) => void
}

export default function UploadPage({ onDatasetLoaded }: UploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [diagnostics, setDiagnostics] = useState<Record<string, SafeAny> | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [datasets, setDatasets] = useState<Record<string, SafeAny>[]>([])
  const [loadingDatasets, setLoadingDatasets] = useState(false)

  const fetchDatasets = useCallback(async () => {
    setLoadingDatasets(true)
    try {
      const list = await listDatasets()
      setDatasets(list)
    } catch (err) {
      console.error('Failed to list datasets:', err)
    } finally {
      setLoadingDatasets(false)
    }
  }, [])

  useEffect(() => {
    fetchDatasets()
  }, [fetchDatasets])

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
    onDatasetLoaded(ds.id || ds.dataset_id, ds.name, {
      rows: ds.rows,
      columns: ds.columns,
    })
  }

  const handleFile = useCallback(async (file: File) => {
    setError(null)
    setResult(null)
    setDiagnostics(null)
    setUploading(true)
    setProgress(10)

    try {
      // Simulate progress stages
      const progressTimer = setInterval(() => {
        setProgress(p => Math.min(p + 15, 85))
      }, 400)

      const data = await uploadDataset(file)

      clearInterval(progressTimer)
      setProgress(100)
      setResult(data)
      setDiagnostics(data.diagnostics || null)

      // Auto-navigate after a longer delay so diagnostics are readable
      setTimeout(() => {
        onDatasetLoaded(data.dataset_id, data.name, {
          rows: data.rows,
          columns: data.columns,
        })
      }, 5000)
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
  }, [onDatasetLoaded])

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
        className="card cursor-pointer transition-all"
        style={{
          padding: '4rem 2rem',
          textAlign: 'center',
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
                  <div className="flex items-center gap-3">
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
        Redirecting to your dashboard...
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
