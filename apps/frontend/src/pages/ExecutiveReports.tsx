/**
 * InsightIQ — Executive Reports
 */

import { useState } from 'react'
import { FileText, Download, FileSpreadsheet, Presentation, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react'
import { getExportUrl } from '../lib/api'
import { useAuth } from '../lib/auth'

interface Props {
  datasetId: string | null
}

export default function ExecutiveReports({ datasetId }: Props) {
  const [exporting, setExporting] = useState<'pdf' | 'ppt' | 'csv' | 'xlsx' | null>(null)
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const { user } = useAuth()

  if (!datasetId) {
    return (
      <div className="text-center py-20 animate-fade-in">
        <FileText size={48} style={{ color: 'var(--color-text-muted)', margin: '0 auto 1rem' }} />
        <h2 className="font-bold text-xl mb-2" style={{ color: 'var(--color-text-primary)' }}>Executive Reports</h2>
        <p style={{ color: 'var(--color-text-secondary)' }}>Upload a dataset to generate downloadable reports.</p>
      </div>
    )
  }

  const handleDownload = async (type: 'pdf' | 'ppt' | 'csv' | 'xlsx') => {
    if ((type === 'pdf' || type === 'ppt') && user?.role === 'guest') {
      window.dispatchEvent(new CustomEvent('insightiq-trigger-signup'))
      return
    }
    setExporting(type)

    setToast(null)
    try {
      const token = localStorage.getItem('insightiq_token')
      const headers: Record<string, string> = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      
      const exportUrl = getExportUrl(datasetId, type)
      const res = await fetch(exportUrl, { headers })
      
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}))
        throw new Error(errBody.detail || `Export failed with status ${res.status}`)
      }
      
      const blob = await res.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      
      const disposition = res.headers.get('content-disposition')
      const extension = type === 'ppt' ? 'pptx' : type === 'xlsx' ? 'xlsx' : type
      let filename = `InsightIQ_Export_${type}_${Date.now()}.${extension}`
      if (disposition && disposition.indexOf('attachment') !== -1) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/
        const matches = filenameRegex.exec(disposition)
        if (matches != null && matches[1]) {
          filename = matches[1].replace(/['"]/g, '')
        }
      }

      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = filename
      
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(downloadUrl)
      
      setToast({
        type: 'success',
        message: `${type.toUpperCase()} downloaded successfully.`
      })
      setTimeout(() => setToast(null), 4000)
    } catch (err: any) {
      console.error(err)
      setToast({
        type: 'error',
        message: err.message || `Failed to generate report. Please try again.`
      })
    } finally {
      setExporting(null)
    }
  }

  return (
    <div className="animate-fade-in max-w-6xl mx-auto space-y-8">
      {/* Toast Notification */}
      {toast && (
        <div className={`fixed bottom-5 right-5 z-50 p-4 rounded-xl shadow-lg flex items-center gap-3 border animate-bounce ${
          toast.type === 'success' 
            ? 'bg-emerald-50 text-emerald-800 border-emerald-200' 
            : 'bg-rose-50 text-rose-800 border-rose-200'
        }`}>
          {toast.type === 'success' ? (
            <CheckCircle2 className="text-emerald-600 flex-shrink-0" size={20} />
          ) : (
            <AlertCircle className="text-rose-600 flex-shrink-0" size={20} />
          )}
          <span className="text-sm font-semibold">{toast.message}</span>
        </div>
      )}

      <div className="page-header mb-8">
        <h1 className="page-title">Executive Reports & Export</h1>
        <p className="page-subtitle">Download AI-generated insights and raw data</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* PDF Export */}
        <div className="card hover:-translate-y-1 transition-transform bg-white border border-slate-200 p-6 rounded-xl shadow-sm flex flex-col justify-between">
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                 style={{ background: 'var(--color-danger-light)', color: 'var(--color-danger)' }}>
              <FileText size={32} />
            </div>
            <h3 className="font-bold text-lg mb-2 text-slate-800">PDF Summary</h3>
            <p className="text-xs text-slate-500 mb-2 leading-relaxed">
              A clean, printable executive summary featuring key KPIs, findings, and analysis.
            </p>
          </div>
          <button
            onClick={() => handleDownload('pdf')}
            disabled={exporting !== null}
            className="btn w-full flex justify-center items-center gap-2 bg-red-600 hover:bg-red-700 text-white rounded-lg py-2 font-semibold text-sm disabled:opacity-50"
          >
            {exporting === 'pdf' ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            {exporting === 'pdf' ? 'Generating PDF...' : 'Download PDF'}
          </button>
        </div>

        {/* PPT Export */}
        <div className="card hover:-translate-y-1 transition-transform bg-white border border-slate-200 p-6 rounded-xl shadow-sm flex flex-col justify-between">
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                 style={{ background: 'var(--color-warning-light)', color: 'var(--color-warning)' }}>
              <Presentation size={32} />
            </div>
            <h3 className="font-bold text-lg mb-2 text-slate-800">PowerPoint</h3>
            <p className="text-xs text-slate-500 mb-2 leading-relaxed">
              A ready-to-present slide deck containing data insights, formatted for boardrooms.
            </p>
          </div>
          <button
            onClick={() => handleDownload('ppt')}
            disabled={exporting !== null}
            className="btn w-full flex justify-center items-center gap-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg py-2 font-semibold text-sm disabled:opacity-50"
          >
            {exporting === 'ppt' ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            {exporting === 'ppt' ? 'Generating PPT...' : 'Download PPT'}
          </button>
        </div>

        {/* CSV Export */}
        <div className="card hover:-translate-y-1 transition-transform bg-white border border-slate-200 p-6 rounded-xl shadow-sm flex flex-col justify-between">
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                 style={{ background: 'var(--color-success-light)', color: 'var(--color-success)' }}>
              <FileSpreadsheet size={32} />
            </div>
            <h3 className="font-bold text-lg mb-2 text-slate-800">Raw Data (CSV)</h3>
            <p className="text-xs text-slate-500 mb-2 leading-relaxed">
              Export the underlying processed dataset as a CSV file for your own models.
            </p>
          </div>
          <button
            onClick={() => handleDownload('csv')}
            disabled={exporting !== null}
            className="btn w-full flex justify-center items-center gap-2 bg-green-600 hover:bg-green-700 text-white rounded-lg py-2 font-semibold text-sm disabled:opacity-50"
          >
            {exporting === 'csv' ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            {exporting === 'csv' ? 'Generating CSV...' : 'Download CSV'}
          </button>
        </div>

        {/* Excel Export */}
        <div className="card hover:-translate-y-1 transition-transform bg-white border border-slate-200 p-6 rounded-xl shadow-sm flex flex-col justify-between">
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                 style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'rgb(37, 99, 235)' }}>
              <FileSpreadsheet size={32} />
            </div>
            <h3 className="font-bold text-lg mb-2 text-slate-800">Excel (XLSX)</h3>
            <p className="text-xs text-slate-500 mb-2 leading-relaxed">
              Export the underlying processed dataset as a formatted Excel spreadsheet.
            </p>
          </div>
          <button
            onClick={() => handleDownload('xlsx')}
            disabled={exporting !== null}
            className="btn w-full flex justify-center items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 font-semibold text-sm disabled:opacity-50"
          >
            {exporting === 'xlsx' ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            {exporting === 'xlsx' ? 'Generating XLSX...' : 'Download Excel'}
          </button>
        </div>
      </div>
    </div>
  )
}
