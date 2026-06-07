/**
 * InsightIQ — Executive Reports
 */

import { FileText, Download, FileSpreadsheet, Presentation } from 'lucide-react'
import { getExportUrl } from '../lib/api'

interface Props {
  datasetId: string | null
}

export default function ExecutiveReports({ datasetId }: Props) {
  if (!datasetId) {
    return (
      <div className="text-center py-20 animate-fade-in">
        <FileText size={48} style={{ color: 'var(--color-text-muted)', margin: '0 auto 1rem' }} />
        <h2 className="font-bold text-xl mb-2" style={{ color: 'var(--color-text-primary)' }}>Executive Reports</h2>
        <p style={{ color: 'var(--color-text-secondary)' }}>Upload a dataset to generate downloadable reports.</p>
      </div>
    )
  }

  const handleDownload = (type: 'pdf' | 'ppt' | 'csv') => {
    // Open the download URL in a new tab to trigger the download
    window.open(getExportUrl(datasetId, type), '_blank')
  }

  return (
    <div className="animate-fade-in max-w-4xl mx-auto">
      <div className="page-header mb-8">
        <h1 className="page-title">Executive Reports & Export</h1>
        <p className="page-subtitle">Download AI-generated insights and raw data</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* PDF Export */}
        <div className="card hover:-translate-y-1 transition-transform">
          <div className="p-6 text-center">
            <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                 style={{ background: 'var(--color-danger-light)', color: 'var(--color-danger)' }}>
              <FileText size={32} />
            </div>
            <h3 className="font-bold text-lg mb-2 text-slate-800">PDF Summary</h3>
            <p className="text-sm text-slate-500 mb-6">
              A clean, printable executive summary featuring key KPIs, findings, and analysis.
            </p>
            <button
              onClick={() => handleDownload('pdf')}
              className="btn w-full flex justify-center bg-red-600 hover:bg-red-700 text-white"
            >
              <Download size={16} /> Download PDF
            </button>
          </div>
        </div>

        {/* PPT Export */}
        <div className="card hover:-translate-y-1 transition-transform">
          <div className="p-6 text-center">
            <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                 style={{ background: 'var(--color-warning-light)', color: 'var(--color-warning)' }}>
              <Presentation size={32} />
            </div>
            <h3 className="font-bold text-lg mb-2 text-slate-800">PowerPoint</h3>
            <p className="text-sm text-slate-500 mb-6">
              A ready-to-present slide deck containing data insights, formatted for boardrooms.
            </p>
            <button
              onClick={() => handleDownload('ppt')}
              className="btn w-full flex justify-center bg-orange-600 hover:bg-orange-700 text-white"
            >
              <Download size={16} /> Download PPT
            </button>
          </div>
        </div>

        {/* CSV Export */}
        <div className="card hover:-translate-y-1 transition-transform">
          <div className="p-6 text-center">
            <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                 style={{ background: 'var(--color-success-light)', color: 'var(--color-success)' }}>
              <FileSpreadsheet size={32} />
            </div>
            <h3 className="font-bold text-lg mb-2 text-slate-800">Raw Data</h3>
            <p className="text-sm text-slate-500 mb-6">
              Export the underlying processed dataset as a CSV file for your own models.
            </p>
            <button
              onClick={() => handleDownload('csv')}
              className="btn w-full flex justify-center bg-green-600 hover:bg-green-700 text-white"
            >
              <Download size={16} /> Download CSV
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
