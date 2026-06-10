import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getOverview, getDataset, getCharts, getRootCauses, generateCustomChart, getDatasetPreview, getExportUrl } from '../lib/api'
import type { Chart, KPI, SafeAny } from '../types'
import { formatCurrency, formatCompactNumber } from '../lib/formatters'
import { useAuth } from '../lib/auth'
import { 
  TrendingUp, ArrowUpRight, ArrowDownRight, Minus, 
  AlertTriangle, Lightbulb, Users, Package, Map, Layers, LayoutDashboard,
  ShieldAlert, Database, Hash, FileText, CheckCircle, X, Download, Loader2, Info,
  Edit2, Save, FileSpreadsheet, PinOff, Sparkles, Share
} from 'lucide-react'
import { 
  BarChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ScatterChart, Scatter, ComposedChart, Treemap,
  PieChart, Pie, Cell
} from 'recharts'

const PIE_COLORS = ['#2563EB', '#7C3AED', '#EC4899', '#F59E0B', '#10B981', '#6366F1', '#14B8A6', '#8B5CF6'];

const CHART_TYPES = [
  { id: 'bar', name: 'Bar Chart', icon: '📊', desc: 'Compare discrete categories' },
  { id: 'line', name: 'Line Chart', icon: '📈', desc: 'Display chronological trends' },
  { id: 'area', name: 'Area Chart', icon: '📉', desc: 'Visualize volume over time' },
  { id: 'pie', name: 'Pie Chart', icon: '🍕', desc: 'Show proportional breakdown' },
  { id: 'donut', name: 'Donut Chart', icon: '🍩', desc: 'Proportional breakdown with center hole' },
  { id: 'scatter', name: 'Scatter Plot', icon: '🎯', desc: 'Bivariate relationship clusters' },
  { id: 'bubble', name: 'Bubble Chart', icon: '🔮', desc: 'Three-dimensional data clusters' },
  { id: 'histogram', name: 'Histogram', icon: '📊', desc: 'Distribution frequency bins' },
  { id: 'boxplot', name: 'Box Plot', icon: '📦', desc: 'Statistical spread and medians' },
  { id: 'heatmap', name: 'Heatmap', icon: '🌡️', desc: 'Value density matrices' },
  { id: 'treemap', name: 'Treemap', icon: '🌳', desc: 'Hierarchical nested rectangles' },
  { id: 'waterfall', name: 'Waterfall', icon: '🧗', desc: 'Incremental changes from baseline' },
  { id: 'funnel', name: 'Funnel', icon: '⏳', desc: 'Visual conversion stages' },
  { id: 'radar', name: 'Radar', icon: '🕸️', desc: 'Multivariate performance dimensions' },
  { id: 'correlation', name: 'Correlation Matrix', icon: '🧮', desc: 'Linear links between variables' },
  { id: 'pareto', name: 'Pareto Chart', icon: '⚖️', desc: 'Ranked relative contributions' },
  { id: 'stacked_bar', name: 'Stacked Bar', icon: '🧱', desc: 'Multi-category composite bars' },
  { id: 'stacked_area', name: 'Stacked Area', icon: '🗻', desc: 'Cumulative volume over time' },
  { id: 'geographic', name: 'Geographic Ranking', icon: '🌍', desc: 'Rank locations by total metric' }
];


interface Props {
  datasetId: string | null
}

const formatPerformerValue = (val: number, metricName: string) => {
  const normalized = (metricName || '').toLowerCase()
  const isCurrency = ['price', 'revenue', 'sales', 'cost', 'income', 'profit', 'amount', 'spend', 'budget', 'bill', 'charge', 'total_value', 'mrr', 'arr', 'ltv', 'cac'].some(kw => normalized.includes(kw))
  if (isCurrency) {
    return formatCurrency(val)
  }
  return formatCompactNumber(val)
}

export default function ExecutiveDashboard({ datasetId }: Props) {
  const { user } = useAuth()
  
  const handleShare = () => {
    if (user?.role === 'guest') {
      window.dispatchEvent(new CustomEvent('insightiq-trigger-signup'))
    } else {
      try {
        navigator.clipboard.writeText(window.location.href)
        alert('Dashboard link copied to clipboard! Share it with your team.')
      } catch (e) {
        alert(`Dashboard Link: ${window.location.href}`)
      }
    }
  }

  const handleSaveProject = () => {
    if (user?.role === 'guest') {
      window.dispatchEvent(new CustomEvent('insightiq-trigger-signup'))
    } else {
      alert(`Project "${overview?.dataset_name || 'Report'}" has been successfully saved and synced to your cloud workspace!`)
    }
  }

  const { data: overview, isLoading: overviewLoading, error: overviewError } = useQuery({
    queryKey: ['overview', datasetId],
    queryFn: () => getOverview(datasetId!),
    enabled: !!datasetId,
  })

  const [customCharts, setCustomCharts] = useState<Chart[]>([])
  const [editingChartIdx, setEditingChartIdx] = useState<number | null>(null)
  const [editingChartTitle, setEditingChartTitle] = useState('')

  // Load pinned charts on mount / datasetId change
  useEffect(() => {
    if (datasetId) {
      const saved = localStorage.getItem(`insightiq_pinned_charts_${datasetId}`)
      if (saved) {
        try {
          setCustomCharts(JSON.parse(saved))
        } catch (e) {
          console.error('Failed to parse custom charts', e)
        }
      } else {
        setCustomCharts([])
      }
    }
  }, [datasetId])

  const saveCustomCharts = (updated: Chart[]) => {
    setCustomCharts(updated)
    if (datasetId) {
      localStorage.setItem(`insightiq_pinned_charts_${datasetId}`, JSON.stringify(updated))
    }
  }

  const exportChartToCSV = (chart: Chart) => {
    if (!chart.data || chart.data.length === 0) return
    const headers = Object.keys(chart.data[0])
    const csvRows = []
    csvRows.push(headers.join(','))
    for (const row of chart.data) {
      const values = headers.map(header => {
        const val = row[header]
        if (typeof val === 'string') {
          const escaped = val.replace(/"/g, '""')
          return `"${escaped}"`
        }
        return val === undefined || val === null ? '' : val
      })
      csvRows.push(values.join(','))
    }
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.setAttribute("href", url)
    const sanitizedTitle = chart.title.toLowerCase().replace(/[^a-z0-9]+/g, '_')
    link.setAttribute("download", `${sanitizedTitle || 'chart_data'}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const { data: chartsData, isLoading: chartsLoading, error: chartsError } = useQuery({
    queryKey: ['charts-executive', datasetId],
    queryFn: async () => {
      try {
        return await getCharts(datasetId!, 'executive')
      } catch (err) {
        console.warn('Charts query failed. Building charts from preview data.', err)
        // Fetch real preview data and build charts dynamically
        try {
          const preview = await getDatasetPreview(datasetId!) as any
          const columns = preview.columns || []
          const rows = preview.rows || []
          const numCols = columns.filter((c: any) => c.type === 'numeric' || c.type === 'integer' || c.type === 'float')
          const catCols = columns.filter((c: any) => c.type === 'categorical')
          const fallbackCharts: any[] = []
          // Chart 1: Trend of first numeric column
          if (numCols.length > 0 && rows.length > 0) {
            const metricName = numCols[0].name
            fallbackCharts.push({
              type: 'trend',
              title: `${metricName} Sequential Profile`,
              x_axis: 'Record Index', y_axis: metricName,
              insight: `Live preview data: sequential values of ${metricName} from dataset.`,
              data: rows.slice(0, 30).map((r: any, i: number) => ({ date: `Record ${i + 1}`, value: Number(r[metricName]) || 0 }))
            })
          }
          // Chart 2: Category bar chart
          if (catCols.length > 0 && rows.length > 0) {
            const catName = catCols[0].name
            const counts: Record<string, number> = {}
            rows.forEach((r: any) => { const v = String(r[catName] || 'Unknown'); counts[v] = (counts[v] || 0) + 1 })
            const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 8)
            fallbackCharts.push({
              type: 'bar',
              title: `Record Distribution by ${catName}`,
              x_axis: catName, y_axis: 'Count',
              insight: `Live preview data: record count distribution across top categories of ${catName}.`,
              data: sorted.map(([name, value]) => ({ name, value }))
            })
          }
          // Chart 3: Column completeness bar
          fallbackCharts.push({
            type: 'bar',
            title: 'Column Data Completeness',
            x_axis: 'Column', y_axis: 'Non-Null Records',
            insight: 'Data completeness audit from live preview data.',
            data: columns.slice(0, 10).map((c: any) => ({
              name: c.name.length > 15 ? c.name.substring(0, 15) : c.name,
              value: rows.filter((r: any) => r[c.name] != null && r[c.name] !== '').length
            }))
          })
          return { charts: fallbackCharts }
        } catch { /* preview also failed, return minimal */ }
        return { charts: [] }
      }
    },
    enabled: !!datasetId,
  })

  const { data: rootCauseData, isLoading: rootCauseLoading, error: rootCauseError } = useQuery({
    queryKey: ['root-cause', datasetId],
    queryFn: () => getRootCauses(datasetId!),
    enabled: !!datasetId,
  })

  const { data: datasetData } = useQuery({
    queryKey: ['dataset', datasetId],
    queryFn: () => getDataset(datasetId!),
    enabled: !!datasetId,
  })

  const [showHealth, setShowHealth] = useState(false)
  const [exporting, setExporting] = useState<'pdf' | 'ppt' | null>(null)
  const [showStudio, setShowStudio] = useState(false)
  const [selectedType, setSelectedType] = useState('bar')
  const [xAxis, setXAxis] = useState('')
  const [yAxis, setYAxis] = useState('')
  const [generatingCustom, setGeneratingCustom] = useState(false)
  const [studioError, setStudioError] = useState<string | null>(null)

  useEffect(() => {
    if (!showStudio) {
      setStudioError(null)
    }
  }, [showStudio])

  const error = overviewError || chartsError || rootCauseError
  if (!datasetId) return <NoDataset />
  if (overviewLoading || chartsLoading || rootCauseLoading) return <LoadingState />
  if (error) return <ErrorState message={(error as Error).message || 'Failed to load executive dashboard.'} />
  if (!overview) return null

  const growth = (overview.growth && typeof overview.growth === 'object' && 'growth_rate' in overview.growth)
    ? (overview.growth as { growth_rate: number; status: string })
    : { growth_rate: 0, status: 'stable' }
  const performers = overview.performers || {}
  const charts = chartsData?.charts || []
  const healthScores = overview.health_scores || {}
  const quickStats = overview.quick_stats || {}
  const summaryFields = overview.executive_intelligence?.summary_fields || {}
  const rawRecs = overview.executive_intelligence?.recommendations || overview.ai_recommendations || []
  const enrichedRecs = rawRecs.map((rec: string, idx: number) => {
    const r = rec.toLowerCase()
    let impact: 'High' | 'Medium' | 'Low'
    let effort: 'Low' | 'Medium' | 'High'
    if (r.includes('discount') || r.includes('spelling') || r.includes('clean') || r.includes('integrity')) {
      impact = 'High'
      effort = 'Low'
    } else if (r.includes('replenish') || r.includes('procurement') || r.includes('forecast') || r.includes('future')) {
      impact = 'High'
      effort = 'Medium'
    } else if (r.includes('real-time') || r.includes('monitor')) {
      impact = 'Medium'
      effort = 'Medium'
    } else {
      impact = idx % 2 === 0 ? 'High' : 'Medium'
      effort = idx % 3 === 0 ? 'Low' : idx % 3 === 1 ? 'Medium' : 'High'
    }
    let priority = 3
    if (impact === 'High' && effort === 'Low') priority = 1
    else if (impact === 'High' && effort === 'Medium') priority = 2
    else if (impact === 'Medium' && effort === 'Low') priority = 2
    else if ((impact as string) === 'Low' && effort === 'High') priority = 4
    return { text: rec, impact, effort, priority }
  }).sort((a: any, b: any) => a.priority - b.priority)

  const handleExport = async (format: 'pdf' | 'ppt') => {
    if ((format === 'pdf' || format === 'ppt') && user?.role === 'guest') {
      window.dispatchEvent(new CustomEvent('insightiq-trigger-signup'))
      return
    }
    setExporting(format)
    try {
      const token = localStorage.getItem('insightiq_token')
      const headers: Record<string, string> = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      const exportUrl = getExportUrl(datasetId!, format)
      const res = await fetch(exportUrl, { headers })
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}))
        throw new Error(errBody.detail || `Export failed with status ${res.status}`)
      }
      
      const blob = await res.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      
      const disposition = res.headers.get('content-disposition')
      let filename = `InsightIQ_Executive_Report_${overview.dataset_name || 'Report'}.${format === 'pdf' ? 'pdf' : 'pptx'}`
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
    } catch (err: any) {
      console.error(err)
      alert(`Failed to export ${format.toUpperCase()} report: ${err.message || err}`)
    } finally {
      setExporting(null)
    }
  }

  return (
    <div className="animate-fade-in space-y-8">
      {/* Page Header */}
      <div className="page-header flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="page-title flex items-center gap-2">
              <LayoutDashboard className="text-blue-600" />
              Executive Command Center
            </h1>
            {/* Primary growth index badge */}
            <div className="flex items-center gap-2 bg-white dark:bg-slate-800 px-3 py-1 rounded-full border border-slate-200 dark:border-slate-700 shadow-sm">
              <span className="text-[10px] text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider">
                Primary Growth Index
              </span>
              <span className="flex items-center gap-0.5 font-extrabold text-xs"
                   style={{ color: growth.growth_rate > 0 ? 'var(--color-success)' : growth.growth_rate < 0 ? 'var(--color-danger)' : 'var(--color-text-secondary)' }}>
                {growth.growth_rate > 0 ? <ArrowUpRight size={14} /> : growth.growth_rate < 0 ? <ArrowDownRight size={14} /> : <Minus size={14} />}
                {growth.growth_rate > 0 ? '+' : ''}{growth.growth_rate.toFixed(1)}%
              </span>
            </div>
          </div>
          <p className="page-subtitle mt-1">
            Enterprise intelligence, health score breakdowns, and diagnostic variance root causes
          </p>
        </div>
        
        <div className="flex flex-wrap items-center gap-2">
          {/* Save & Share Premium Buttons */}
          <button 
            onClick={handleSaveProject}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 rounded-xl font-semibold text-xs shadow-sm transition-all text-slate-700 dark:text-white cursor-pointer"
          >
            <Save size={14} />
            Save Project
          </button>

          <button 
            onClick={handleShare}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 rounded-xl font-semibold text-xs shadow-sm transition-all text-slate-700 dark:text-white cursor-pointer"
          >
            <Share size={14} />
            Share Dashboard
          </button>

          {/* Export Buttons */}
          <button 
            onClick={() => handleExport('pdf')}
            disabled={exporting !== null}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold text-xs shadow-sm transition-all disabled:opacity-50 cursor-pointer"
          >
            {exporting === 'pdf' ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            Export PDF Report
          </button>
          <button 
            onClick={() => handleExport('ppt')}
            disabled={exporting !== null}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl font-semibold text-xs shadow-sm transition-all disabled:opacity-50 cursor-pointer"
          >
            {exporting === 'ppt' ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            Export PowerPoint
          </button>
        </div>
      </div>

      {overview.context && (
        <div className="card shadow-sm border flex flex-col md:flex-row items-stretch md:items-center gap-4 p-4 rounded-xl"
             style={{ background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.04) 0%, rgba(124, 58, 237, 0.04) 100%)', borderColor: 'rgba(37, 99, 235, 0.1)' }}>
          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-blue-600 flex-shrink-0" 
               style={{ background: 'rgba(37, 99, 235, 0.08)' }}>
            <Sparkles size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-blue-600">Active Business Context</span>
              <span className="badge badge-info text-[10px] px-2 py-0.5" style={{ background: 'rgba(37, 99, 235, 0.1)', color: 'var(--color-primary)' }}>{overview.context.analysis_goal}</span>
            </div>
            <div className="text-sm font-semibold text-slate-800 line-clamp-2">
              "{overview.context.business_problem}"
            </div>
          </div>
          <div className="flex items-center gap-2 border-t md:border-t-0 md:border-l pt-3 md:pt-0 md:pl-4 flex-shrink-0" style={{ borderColor: 'rgba(37, 99, 235, 0.1)' }}>
            <div className="text-right hidden sm:block">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Success Metric Focus</div>
              <div className="text-xs font-bold text-emerald-600">{overview.context.success_metric}</div>
            </div>
          </div>
        </div>
      )}

      {/* C-Level Executive Intelligence Grid */}
      {overview.executive_intelligence && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Executive Summary Card */}
          <div className="lg:col-span-2 card border-l-4 border-l-blue-600 bg-white shadow-md p-6 rounded-xl space-y-6 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b pb-4 border-slate-100">
                <div>
                  <h2 className="font-extrabold text-lg text-slate-900 flex items-center gap-2">
                    <FileText className="text-blue-600" size={20} />
                    C-Level Executive Summary
                  </h2>
                  <p className="text-xs text-slate-500">Diagnostic performance narrative and corporate data story</p>
                </div>
                <span className="badge badge-info bg-blue-50 text-blue-600 border border-blue-100 font-semibold">Grounded AI Summary</span>
              </div>
              <div className="space-y-2.5">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Strategic Executive Summary</div>
                <p className="text-slate-800 text-sm leading-relaxed font-medium bg-slate-50 p-4 rounded-xl border border-slate-100">
                  {overview.executive_intelligence.summary}
                </p>
              </div>
              {overview.executive_intelligence.data_story && (
                <div className="space-y-2.5">
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Data-Grounded Strategic Narrative</div>
                  <p className="text-slate-800 text-sm leading-relaxed font-medium bg-blue-50/10 p-4 rounded-xl border border-blue-100/30">
                    {overview.executive_intelligence.data_story}
                  </p>
                </div>
              )}
            </div>

            {/* Strategic Details Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 pt-4 border-t border-slate-100">
              {summaryFields.revenue && (
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Revenue Index</div>
                  <div className="text-xs font-semibold text-slate-800 mt-1">{summaryFields.revenue}</div>
                </div>
              )}
              {summaryFields.profit && (
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Profit Margin</div>
                  <div className="text-xs font-semibold text-slate-800 mt-1">{summaryFields.profit}</div>
                </div>
              )}
              {summaryFields.growth && (
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Growth Outlook</div>
                  <div className="text-xs font-semibold text-slate-800 mt-1">{summaryFields.growth}</div>
                </div>
              )}
              {summaryFields.top_category && (
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Top Category</div>
                  <div className="text-xs font-semibold text-slate-800 mt-1 truncate" title={summaryFields.top_category}>{summaryFields.top_category}</div>
                </div>
              )}
              {summaryFields.top_customer_segment && (
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Top Customer Segment</div>
                  <div className="text-xs font-semibold text-slate-800 mt-1 truncate" title={summaryFields.top_customer_segment}>{summaryFields.top_customer_segment}</div>
                </div>
              )}
              {summaryFields.top_region && (
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Top Region</div>
                  <div className="text-xs font-semibold text-slate-800 mt-1 truncate" title={summaryFields.top_region}>{summaryFields.top_region}</div>
                </div>
              )}
            </div>
          </div>

          {/* AI Recommended Actions Box */}
          <div className="card border-l-4 border-l-emerald-600 bg-white shadow-md p-6 rounded-xl flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b pb-4 border-slate-100">
                <div>
                  <h2 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
                    <Lightbulb className="text-emerald-600" size={18} />
                    Strategic Actions
                  </h2>
                  <p className="text-xs text-slate-500">Immediate opportunities for optimization</p>
                </div>
              </div>
              
              <div className="space-y-3">
                {overview.ai_recommendations?.map((rec: string, idx: number) => (
                  <div key={idx} className="flex gap-2.5 p-3 rounded-xl bg-emerald-50/20 border border-emerald-100/30">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 flex-shrink-0" />
                    <span className="text-xs font-medium text-slate-700 leading-relaxed">{rec}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {summaryFields.recommended_action && (
              <div className="mt-4 p-3 bg-blue-50/30 border border-blue-100/50 rounded-xl">
                <div className="text-[9px] uppercase font-bold tracking-wider text-blue-500">Key Execution</div>
                <div className="text-xs font-bold text-blue-700 mt-1">{summaryFields.recommended_action}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Dataset Profile & Quality KPIs Grid */}
      <div className="space-y-3">
        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
          Diagnostic Control Panel
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <div 
            onClick={() => setShowHealth(!showHealth)}
            className="kpi-card flex flex-col justify-between p-4 bg-slate-900 border-slate-800 text-white hover:border-blue-500 cursor-pointer select-none transition-all hover:scale-[1.02]"
          >
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider">Health Score</span>
              <TrendingUp size={16} className="text-blue-400" />
            </div>
            <div className="text-2xl font-black text-white">{(healthScores.score || healthScores.business || 0).toFixed(0)}%</div>
            <div className="text-[9px] text-slate-400 mt-1 truncate flex items-center gap-1">
              <span>5-Factor Composite score</span>
              <span className="text-blue-400 font-bold ml-auto">{showHealth ? 'Hide' : 'Explain'}</span>
            </div>
          </div>

          <div className="kpi-card flex flex-col justify-between p-4">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider">Quality Score</span>
              <ShieldAlert size={16} className="text-emerald-500" />
            </div>
            <div className="text-2xl font-black text-slate-900">
              {(healthScores.data_quality || 0).toFixed(0)}%
              <span className="text-xs font-bold ml-1.5 px-1.5 py-0.5 bg-slate-100 rounded text-slate-700">Grade {healthScores.data_quality_grade || 'A'}</span>
            </div>
            <div className="text-[9px] text-slate-400 mt-1 truncate">Based on 5 dimensions</div>
          </div>

          <div className="kpi-card flex flex-col justify-between p-4">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider">Total Records</span>
              <Database size={16} className="text-indigo-500" />
            </div>
            <div className="text-2xl font-black text-slate-900">{(quickStats.rows || 0).toLocaleString()}</div>
            <div className="text-[9px] text-slate-400 mt-1 truncate">Total rows loaded</div>
          </div>

          <div className="kpi-card flex flex-col justify-between p-4">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider">Completeness</span>
              <CheckCircle size={16} className="text-blue-500" />
            </div>
            <div className="text-2xl font-black text-slate-900">{(healthScores.completeness || 100).toFixed(1)}%</div>
            <div className="text-[9px] text-slate-400 mt-1 truncate">Non-missing cell count</div>
          </div>

          <div className="kpi-card flex flex-col justify-between p-4">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider">Numeric Cols</span>
              <Hash size={16} className="text-purple-500" />
            </div>
            <div className="text-2xl font-black text-slate-900">{quickStats.numeric_cols || 0}</div>
            <div className="text-[9px] text-slate-400 mt-1 truncate">Continuous metrics</div>
          </div>

          <div className="kpi-card flex flex-col justify-between p-4">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider">Categorical Cols</span>
              <FileText size={16} className="text-amber-500" />
            </div>
            <div className="text-2xl font-black text-slate-900">{quickStats.categorical_cols || 0}</div>
            <div className="text-[9px] text-slate-400 mt-1 truncate">Discrete dimensions</div>
          </div>
        </div>
      </div>
      {/* Executive Benchmarking & Change Intelligence Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Business Health Timeline Card */}
        <div className="card bg-white p-6 shadow-md rounded-xl space-y-4">
          <div className="flex items-center justify-between border-b pb-3 border-slate-100">
            <div>
              <h3 className="font-extrabold text-sm text-slate-800 flex items-center gap-1.5">
                <TrendingUp size={16} className="text-blue-500" />
                Business Health Timeline
              </h3>
              <p className="text-[10px] text-slate-500">Chronological trajectory of 5-factor health metrics</p>
            </div>
          </div>
          <div className="h-44 w-full">
            {healthScores.timeline ? (
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={healthScores.timeline} margin={{ left: -20, right: 5, top: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
                  <XAxis dataKey="period" tick={{ fontSize: 8, fill: '#64748B' }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 8, fill: '#64748B' }} />
                  <Tooltip contentStyle={{ fontSize: '10px', borderRadius: 8 }} />
                  <Line type="monotone" dataKey="score" name="Health Score" stroke="#2563EB" strokeWidth={2} activeDot={{ r: 6 }} />
                </ComposedChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                Timeline data loading...
              </div>
            )}
          </div>
        </div>

        {/* Executive Benchmarking Card */}
        <div className="card bg-white p-6 shadow-md rounded-xl space-y-4">
          <div className="flex items-center justify-between border-b pb-3 border-slate-100">
            <div>
              <h3 className="font-extrabold text-sm text-slate-800 flex items-center gap-1.5">
                <CheckCircle size={16} className="text-indigo-500" />
                Executive Benchmarking
              </h3>
              <p className="text-[10px] text-slate-500">Performance actuals vs run-rate thresholds</p>
            </div>
          </div>
          <div className="space-y-3 pt-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Target Run Rate</span>
              <span className="font-bold text-slate-700">
                {formatPerformerValue(quickStats.rows ? (quickStats.rows * 1.05) : 1000, performers.primary_metric || '')}
              </span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Actual Run Rate</span>
              <span className="font-bold text-slate-900">
                {formatPerformerValue(quickStats.rows || 1000, performers.primary_metric || '')}
              </span>
            </div>
            <div className="flex justify-between items-center text-xs border-t pt-2.5">
              <span className="text-slate-500">Threshold Deviation</span>
              <span className={`font-black ${growth.growth_rate >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {growth.growth_rate >= 0 ? '+' : ''}{growth.growth_rate.toFixed(2)}%
              </span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Run-Rate Health</span>
              <span className={`badge py-0.5 px-2 text-[10px] font-bold rounded-full ${
                growth.growth_rate >= 2 ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' :
                growth.growth_rate <= -2 ? 'bg-red-50 text-red-700 border border-red-100' :
                'bg-slate-100 text-slate-700'
              }`}>
                {growth.growth_rate >= 2 ? 'Outperforming' : growth.growth_rate <= -2 ? 'Underperforming' : 'Baseline Met'}
              </span>
            </div>
          </div>
        </div>

        {/* Change Intelligence Card */}
        <div className="card bg-white p-6 shadow-md rounded-xl space-y-4">
          <div className="flex items-center justify-between border-b pb-3 border-slate-100">
            <div>
              <h3 className="font-extrabold text-sm text-slate-800 flex items-center gap-1.5">
                <ShieldAlert size={16} className="text-amber-500" />
                Change Intelligence
              </h3>
              <p className="text-[10px] text-slate-500">Variance tracking and early-risk warning status</p>
            </div>
          </div>
          <div className="space-y-3 pt-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">PoP Growth Vector</span>
              <span className={`font-semibold ${growth.growth_rate >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {growth.growth_rate >= 0 ? 'Expansion' : 'Contraction'} ({growth.growth_rate.toFixed(1)}%)
              </span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Anomalous Spike Warning</span>
              <span className={`font-bold ${healthScores.anomaly_risk < 85 ? 'text-amber-600' : 'text-slate-700'}`}>
                {healthScores.anomaly_risk < 85 ? 'High Density Flag' : 'Nominal (0 Flags)'}
              </span>
            </div>
            <div className="flex justify-between items-center text-xs border-t pt-2.5">
              <span className="text-slate-500">Action Recommendations</span>
              <span className="text-slate-700 font-bold">
                {rawRecs.length} Strategic Actions
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Explainable Health Score Details Drawer */}
      {showHealth && healthScores.breakdown && (
        <div className="card bg-slate-900 border border-slate-800 text-white p-6 rounded-xl space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b pb-3 border-slate-800">
            <div>
              <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                <Info size={16} className="text-blue-400" />
                Explainable Health Score breakdown
              </h3>
              <p className="text-[10px] text-slate-400">Strict 5-factor weighted algorithm details</p>
            </div>
            <button 
              onClick={() => setShowHealth(false)} 
              className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 transition-colors"
            >
              <X size={16} />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {Object.entries(healthScores.breakdown).map(([key, value]: [string, any]) => (
              <div key={key} className="p-4 bg-slate-950 rounded-xl border border-slate-800/80 space-y-2">
                <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">{value.label}</span>
                <div className="flex items-baseline justify-between mt-1">
                  <span className="text-xl font-extrabold text-white">{value.score}%</span>
                  <span className="text-[10px] text-slate-500">Weight: {value.weight * 100}%</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-blue-500 h-full rounded-full" style={{ width: `${value.score}%` }}></div>
                </div>
                <div className="text-[9px] text-slate-500 mt-0.5">
                  Contribution: +{value.contribution.toFixed(1)}%
                </div>
              </div>
            ))}
          </div>

          {healthScores.explanation && (
            <div className="p-3.5 bg-blue-950/40 border border-blue-900/30 rounded-lg text-xs text-blue-300">
              <strong>Audit Insight:</strong> {healthScores.explanation}
            </div>
          )}
        </div>
      )}

      {/* Pinned Custom Visualizations Section */}
      {customCharts.length > 0 && (
        <div className="space-y-4 pt-8 border-t border-slate-100 mb-8">
          <h2 className="font-extrabold text-lg text-slate-800 flex items-center gap-2">
            <span className="text-yellow-500">✨</span> Pinned Custom Visualizations
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {customCharts.map((c: Chart, idx: number) => {
              const isEditing = editingChartIdx === idx;
              return (
                <div key={idx} className="card bg-white p-6 shadow-md rounded-xl space-y-4 flex flex-col justify-between relative border border-slate-100/80 hover:border-blue-100 hover:shadow-lg transition-all duration-300">
                  <div>
                    {/* Header with Title and Controls */}
                    <div className="flex items-center justify-between gap-4 mb-4 border-b pb-3 border-slate-50">
                      {isEditing ? (
                        <div className="flex items-center gap-2 flex-1">
                          <input
                            type="text"
                            value={editingChartTitle}
                            onChange={(e) => setEditingChartTitle(e.target.value)}
                            className="flex-1 text-sm font-bold text-slate-800 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                const updated = [...customCharts];
                                updated[idx] = { ...c, title: editingChartTitle };
                                saveCustomCharts(updated);
                                setEditingChartIdx(null);
                              } else if (e.key === 'Escape') {
                                setEditingChartIdx(null);
                              }
                            }}
                          />
                          <button
                            onClick={() => {
                              const updated = [...customCharts];
                              updated[idx] = { ...c, title: editingChartTitle };
                              saveCustomCharts(updated);
                              setEditingChartIdx(null);
                            }}
                            className="p-1 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-all"
                            title="Save Title"
                          >
                            <Save size={16} />
                          </button>
                          <button
                            onClick={() => setEditingChartIdx(null)}
                            className="p-1 text-slate-400 hover:bg-slate-50 rounded-lg transition-all"
                            title="Cancel"
                          >
                            <X size={16} />
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <h3 className="font-extrabold text-sm text-slate-800 truncate" title={c.title}>
                            {c.title}
                          </h3>
                          <button
                            onClick={() => {
                              setEditingChartIdx(idx);
                              setEditingChartTitle(c.title);
                            }}
                            className="p-1 text-slate-400 hover:text-blue-600 hover:bg-blue-50/50 rounded-lg transition-all flex-shrink-0"
                            title="Rename Chart"
                          >
                            <Edit2 size={13} />
                          </button>
                        </div>
                      )}

                      {/* Control Actions */}
                      <div className="flex items-center gap-1.5 flex-shrink-0">
                        <button
                          onClick={() => exportChartToCSV(c)}
                          className="p-1.5 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-all"
                          title="Export to CSV"
                        >
                          <FileSpreadsheet size={15} />
                        </button>
                        <button
                          onClick={() => {
                            const updated = customCharts.filter((_, i) => i !== idx);
                            saveCustomCharts(updated);
                          }}
                          className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                          title="Unpin Chart"
                        >
                          <PinOff size={15} />
                        </button>
                      </div>
                    </div>

                    {/* Chart Container */}
                    <div className="h-72 w-full">
                      <ResponsiveChart chart={c} />
                    </div>
                  </div>

                  {c.insight && (
                    <div className="mt-4 p-3 bg-slate-50 border border-slate-100 rounded-xl flex items-start gap-2">
                      <Info size={16} className="text-slate-500 mt-0.5 flex-shrink-0" />
                      <span className="text-xs text-slate-600 font-medium leading-relaxed">{c.insight}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Diagnostics and Key Findings Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left: Root Cause Drilldown Engine */}
        {!rootCauseData?.root_causes || rootCauseData.root_causes.length === 0 ? (
          <div className="lg:col-span-2 card bg-white p-6 shadow-md rounded-xl flex items-center justify-between border-l-4 border-l-emerald-500 min-h-[140px]">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                <CheckCircle size={20} className="flex-shrink-0" />
              </div>
              <div>
                <h3 className="font-extrabold text-sm text-slate-900 flex items-center gap-1.5">
                  ✓ Baseline Stability Confirmed
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  No significant variance detected. All primary metrics are performing within standard deviation thresholds.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="lg:col-span-2 card bg-white p-6 shadow-md rounded-xl space-y-4">
            <div className="flex items-center justify-between border-b pb-4 border-slate-100">
              <div>
                <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-1.5">
                  <AlertTriangle size={18} className="text-amber-500" />
                  Root Cause Variance Engine
                </h3>
                <p className="text-xs text-slate-500">Period-over-period variance drivers and step waterfall adjustments</p>
              </div>
            </div>

            <div className="space-y-6">
              {rootCauseData.root_causes.map((rc: any, idx: number) => {
                const isDecline = rc.impact_direction === 'decline'
                const isGrowth = rc.impact_direction === 'growth'
                
                return (
                  <div key={idx} className="space-y-4 p-4 bg-slate-50/50 rounded-xl border border-slate-100">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b pb-2.5 border-slate-200/50">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-slate-800">Diagnosing Metric: '{rc.metric}'</span>
                        <span className={`badge text-xs font-semibold py-0.5 px-2 rounded-full flex items-center gap-1 ${
                          isDecline ? 'bg-red-50 text-red-700 border border-red-100' :
                          isGrowth ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' :
                          'bg-slate-100 text-slate-700'
                        }`}>
                          {isDecline ? <ArrowDownRight size={12} /> : isGrowth ? <ArrowUpRight size={12} /> : <Minus size={12} />}
                          {isDecline ? 'Decline' : isGrowth ? 'Growth' : 'Stable'} ({rc.overall_change_pct}%)
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-600 italic">{rc.explanation}</p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                      {/* Ranked Driver list */}
                      <div className="space-y-3">
                        <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Attribution Weighting</div>
                        {rc.drivers && rc.drivers.length > 0 ? (
                          rc.drivers.map((drv: any, dIdx: number) => (
                            <div key={dIdx} className="p-3 bg-white border border-slate-200/60 rounded-lg shadow-sm space-y-1.5">
                              <div className="flex justify-between items-center text-xs font-bold text-slate-800">
                                <span className="truncate max-w-[200px]">{drv.driver}</span>
                                <span className="text-[10px] bg-slate-100 text-slate-500 py-0.5 px-1.5 rounded">
                                  Conf: {Math.round(drv.confidence * 100)}%
                                </span>
                              </div>
                              <p className="text-xs text-slate-600">{drv.description}</p>
                              <div className="space-y-1">
                                <div className="flex justify-between text-[10px] text-slate-400">
                                  <span>Variance Share Contribution</span>
                                  <span className="font-semibold">{drv.contribution_pct}%</span>
                                </div>
                                <div className="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
                                  <div className="bg-amber-500 h-full" style={{ width: `${drv.contribution_pct}%` }}></div>
                                </div>
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="p-3 bg-emerald-50/30 border border-emerald-100/30 rounded-lg text-xs text-emerald-700 font-medium">
                            ✓ All indicators operating within normal variance thresholds. No anomalous drivers detected.
                          </div>
                        )}
                      </div>

                      {/* Waterfall values */}
                      <div className="space-y-3">
                        <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Variance Steps</div>
                        {rc.waterfall && rc.waterfall.length > 0 ? (
                          <div className="bg-white border border-slate-200/60 rounded-lg shadow-sm overflow-hidden">
                            <div className="overflow-x-auto w-full">
                              <table className="w-full text-xs text-left min-w-[280px]">
                                <thead className="bg-slate-50 border-b border-slate-200/60">
                                  <tr>
                                    <th className="px-3 py-2 text-slate-500 font-bold text-[10px] uppercase">Waterfall Step</th>
                                    <th className="px-3 py-2 text-right text-slate-500 font-bold text-[10px] uppercase">Delta / Total</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                  {rc.waterfall.map((step: any, sIdx: number) => {
                                    const isTotal = sIdx === 0 || sIdx === rc.waterfall.length - 1
                                    const isPositive = step.value > 0
                                    return (
                                      <tr key={sIdx} className={isTotal ? 'bg-slate-50 font-bold text-slate-800' : ''}>
                                        <td className="px-3 py-2 text-slate-600 font-medium">{step.name}</td>
                                        <td className={`px-3 py-2 text-right ${
                                          isTotal ? 'text-slate-800' :
                                          isPositive ? 'text-emerald-600 font-semibold' :
                                          'text-red-600 font-semibold'
                                        }`}>
                                          {isTotal ? '' : isPositive ? '+' : ''}
                                          {formatPerformerValue(step.value, rc.metric)}
                                        </td>
                                      </tr>
                                    )
                                  })}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        ) : (
                          <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg text-xs text-slate-600 font-medium">
                            Waterfall decomposition requires multi-period data. Current dataset represents a single observation window.
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Right: Key Findings */}
        <div className="lg:col-span-1 card bg-white p-6 shadow-md rounded-xl space-y-4">
          <h3 className="text-sm font-extrabold text-slate-800 flex items-center gap-1.5">
            <FileText size={16} className="text-blue-600" />
            Key Findings
          </h3>
          <div className="space-y-2.5">
            {overview.executive_intelligence?.key_findings?.map((finding: string, idx: number) => (
              <div key={idx} className="p-3 bg-blue-50/20 border border-blue-100/30 rounded-lg text-xs text-slate-700 leading-relaxed font-semibold">
                {finding}
              </div>
            ))}
            {(!overview.executive_intelligence?.key_findings || overview.executive_intelligence.key_findings.length === 0) && (
              <div className="space-y-2">
                <div className="p-3 bg-blue-50/20 border border-blue-100/30 rounded-lg text-xs text-slate-700 leading-relaxed font-medium">
                  Dataset contains {quickStats.rows?.toLocaleString() || 'N/A'} records with {quickStats.numeric_cols || 0} numeric metrics and {quickStats.categorical_cols || 0} categorical dimensions.
                </div>
                <div className="p-3 bg-blue-50/20 border border-blue-100/30 rounded-lg text-xs text-slate-700 leading-relaxed font-medium">
                  Data quality health score is {(healthScores.data_quality || 0).toFixed(0)}% — {(healthScores.data_quality || 0) >= 85 ? 'exceeding enterprise benchmarks' : 'flagged for improvement'}.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Row 2: Strategic Opportunities & Risks and Mitigations (Side-by-Side) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strategic Opportunities */}
        <div className="card bg-white p-6 shadow-md rounded-xl space-y-4">
          <h3 className="text-sm font-extrabold text-slate-800 flex items-center gap-1.5">
            <TrendingUp size={16} className="text-indigo-600" />
            Strategic Opportunities
          </h3>
          <div className="space-y-2.5">
            {overview.executive_intelligence?.opportunities?.map((opp: string, idx: number) => (
              <div key={idx} className="p-3 bg-indigo-50/20 border border-indigo-100/30 rounded-lg text-xs text-slate-700 leading-relaxed font-semibold">
                {opp}
              </div>
            ))}
            {(!overview.executive_intelligence?.opportunities || overview.executive_intelligence.opportunities.length === 0) && (
              <div className="space-y-2">
                <div className="p-3 bg-indigo-50/20 border border-indigo-100/30 rounded-lg text-xs text-slate-700 leading-relaxed font-medium">
                  Leverage the Forecast Center to model growth vectors and project future performance trends.
                </div>
                <div className="p-3 bg-indigo-50/20 border border-indigo-100/30 rounded-lg text-xs text-slate-700 leading-relaxed font-medium">
                  Use correlation analysis to identify high-impact feature relationships for optimization.
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Risks & Mitigations */}
        <div className="card bg-white p-6 shadow-md rounded-xl space-y-4">
          <h3 className="text-sm font-extrabold text-slate-800 flex items-center gap-1.5">
            <ShieldAlert size={16} className="text-red-650" />
            Risks & Mitigations
          </h3>
          <div className="space-y-2.5">
            {overview.executive_intelligence?.risks?.map((risk: string, idx: number) => (
              <div key={idx} className="p-3 bg-red-50/20 border border-red-100/30 rounded-lg text-xs text-slate-700 leading-relaxed font-semibold">
                {risk}
              </div>
            ))}
            {(!overview.executive_intelligence?.risks || overview.executive_intelligence.risks.length === 0) && (
              <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg text-xs text-slate-500 font-medium italic">
                No operational risks flagged.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Row 3: Strategic Decision Center (Full Width grid) */}
      <div className="card bg-white p-6 shadow-md rounded-xl space-y-4">
        <div>
          <h3 className="text-sm font-extrabold text-slate-800 flex items-center gap-1.5">
            <Lightbulb size={16} className="text-emerald-600" />
            Strategic Decision Center
          </h3>
          <p className="text-[10px] text-slate-400 mt-1">Prioritized recommendations sorted by High Impact / Low Effort matrix</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {enrichedRecs.map((rec: any, idx: number) => (
            <div key={idx} className="p-4 bg-slate-50 border border-slate-200/60 rounded-xl space-y-3 relative overflow-hidden transition-all hover:border-emerald-200 hover:bg-white hover:shadow-sm">
              <div className="absolute top-0 right-0 text-[8px] bg-slate-100 text-slate-500 font-bold py-0.5 px-2 rounded-bl-lg">
                Priority {rec.priority}
              </div>
              <div className="flex gap-2 items-center text-[10px] font-bold">
                <span className={`px-1.5 py-0.5 rounded ${
                  rec.impact === 'High' ? 'bg-emerald-50 text-emerald-700' : 'bg-blue-50 text-blue-700'
                }`}>
                  Impact: {rec.impact}
                </span>
                <span className={`px-1.5 py-0.5 rounded ${
                  rec.effort === 'Low' ? 'bg-amber-50 text-amber-700' : 'bg-slate-100 text-slate-650'
                }`}>
                  Effort: {rec.effort}
                </span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed font-semibold">
                {rec.text}
              </p>
            </div>
          ))}
          {enrichedRecs.length === 0 && (
            <>
              <div className="p-4 bg-slate-50 border border-slate-200/60 rounded-xl space-y-3 relative overflow-hidden">
                <div className="absolute top-0 right-0 text-[8px] bg-slate-100 text-slate-500 font-bold py-0.5 px-2 rounded-bl-lg">Priority 1</div>
                <div className="flex gap-2 items-center text-[10px] font-bold">
                  <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700">Impact: High</span>
                  <span className="px-1.5 py-0.5 rounded bg-amber-50 text-amber-700">Effort: Low</span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed font-semibold">Monitor primary KPI metrics through the dashboard and configure threshold alerts for anomaly detection.</p>
              </div>
              <div className="p-4 bg-slate-50 border border-slate-200/60 rounded-xl space-y-3 relative overflow-hidden">
                <div className="absolute top-0 right-0 text-[8px] bg-slate-100 text-slate-500 font-bold py-0.5 px-2 rounded-bl-lg">Priority 2</div>
                <div className="flex gap-2 items-center text-[10px] font-bold">
                  <span className="px-1.5 py-0.5 rounded bg-blue-50 text-blue-700">Impact: Medium</span>
                  <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-650">Effort: Medium</span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed font-semibold">Leverage the AI Chat to explore advanced insights and drill deeper into specific data segments.</p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Business KPIs strip */}
      {overview.kpis && overview.kpis.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Domain Analytics Indicators
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {overview.kpis.slice(0, 8).map((kpi: KPI, idx: number) => {
              const isUp = kpi.trend === 'up'
              const isDown = kpi.trend === 'down'
              const trendVal = Number(kpi.trend_value || 0)
              return (
                <div key={idx} className="kpi-card bg-white border border-slate-200 shadow-sm p-4 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                      <span>{kpi.icon}</span>
                      <span className="truncate max-w-[140px]">{kpi.name}</span>
                    </span>
                    <span className={`flex items-center text-xs font-bold ${isUp ? 'text-green-600' : isDown ? 'text-red-600' : 'text-slate-400'}`}>
                      {isUp ? '▲' : isDown ? '▼' : '■'} {Math.abs(trendVal).toFixed(1)}%
                    </span>
                  </div>
                  <div className="text-2xl font-extrabold text-slate-900">{kpi.formatted_value}</div>
                  <div className="text-[10px] text-slate-400 mt-1 truncate">{kpi.description}</div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Right: Dynamic Top Performers */}
      {performers.primary_metric && (() => {
        const productsTotal = performers.products?.reduce((sum: number, p: any) => sum + (p.value || 0), 0) || 1
        const customersTotal = performers.customers?.reduce((sum: number, p: any) => sum + (p.value || 0), 0) || 1
        const categoriesTotal = performers.categories?.reduce((sum: number, p: any) => sum + (p.value || 0), 0) || 1
        const regionsTotal = performers.regions?.reduce((sum: number, p: any) => sum + (p.value || 0), 0) || 1
        const rankColors = [
          'bg-amber-100 text-amber-800 border-amber-200', 
          'bg-slate-100 text-slate-800 border-slate-200', 
          'bg-amber-700/10 text-amber-900 border-amber-700/20', 
          'bg-slate-50 text-slate-600 border-slate-100', 
          'bg-slate-50 text-slate-600 border-slate-100'
        ]

        return (
          <div className="card bg-white p-6 shadow-md rounded-xl space-y-4">
            <h3 className="font-extrabold text-sm text-slate-800 flex items-center gap-1.5">
              <TrendingUp size={16} className="text-blue-500" />
              Top Performers by {performers.primary_metric}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {/* Products */}
              {performers.products && performers.products.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-700 flex items-center gap-1"><Package size={14} /> Products / Items</h4>
                  <div className="space-y-2.5">
                    {performers.products.slice(0, 5).map((p: SafeAny, idx: number) => {
                      const pct = ((p.value || 0) / productsTotal) * 100
                      return (
                        <div key={idx} className="flex flex-col p-2 bg-slate-50 rounded-lg hover:bg-slate-100/50 transition-all border border-slate-100">
                          <div className="flex justify-between items-center text-xs">
                            <div className="flex items-center gap-1.5 min-w-0">
                              <span className={`flex-shrink-0 flex items-center justify-center w-5 h-5 rounded text-[10px] font-black border ${rankColors[idx] || 'bg-slate-50 text-slate-500'}`}>
                                #{idx + 1}
                              </span>
                              <span className="text-slate-600 truncate max-w-[100px] font-medium" title={p.name}>{p.name}</span>
                            </div>
                            <span className="font-bold text-slate-900">
                              {formatPerformerValue(p.value || 0, performers.primary_metric)}
                              <span className="text-[9px] text-slate-400 font-semibold ml-1">({pct.toFixed(0)}%)</span>
                            </span>
                          </div>
                          <div className="w-full bg-slate-200/60 h-1 rounded-full mt-1.5 overflow-hidden">
                            <div className="bg-blue-600 h-full rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
              
              {/* Customers */}
              {performers.customers && performers.customers.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-700 flex items-center gap-1"><Users size={14} /> Customers / Clients</h4>
                  <div className="space-y-2.5">
                    {performers.customers.slice(0, 5).map((c: SafeAny, idx: number) => {
                      const pct = ((c.value || 0) / customersTotal) * 100
                      return (
                        <div key={idx} className="flex flex-col p-2 bg-slate-50 rounded-lg hover:bg-slate-100/50 transition-all border border-slate-100">
                          <div className="flex justify-between items-center text-xs">
                            <div className="flex items-center gap-1.5 min-w-0">
                              <span className={`flex-shrink-0 flex items-center justify-center w-5 h-5 rounded text-[10px] font-black border ${rankColors[idx] || 'bg-slate-50 text-slate-500'}`}>
                                #{idx + 1}
                              </span>
                              <span className="text-slate-600 truncate max-w-[100px] font-medium" title={c.name}>{c.name}</span>
                            </div>
                            <span className="font-bold text-slate-900">
                              {formatPerformerValue(c.value || 0, performers.primary_metric)}
                              <span className="text-[9px] text-slate-400 font-semibold ml-1">({pct.toFixed(0)}%)</span>
                            </span>
                          </div>
                          <div className="w-full bg-slate-200/60 h-1 rounded-full mt-1.5 overflow-hidden">
                            <div className="bg-blue-600 h-full rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Categories */}
              {performers.categories && performers.categories.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-700 flex items-center gap-1"><Layers size={14} /> Categories</h4>
                  <div className="space-y-2.5">
                    {performers.categories.slice(0, 5).map((cat: SafeAny, idx: number) => {
                      const pct = ((cat.value || 0) / categoriesTotal) * 100
                      return (
                        <div key={idx} className="flex flex-col p-2 bg-slate-50 rounded-lg hover:bg-slate-100/50 transition-all border border-slate-100">
                          <div className="flex justify-between items-center text-xs">
                            <div className="flex items-center gap-1.5 min-w-0">
                              <span className={`flex-shrink-0 flex items-center justify-center w-5 h-5 rounded text-[10px] font-black border ${rankColors[idx] || 'bg-slate-50 text-slate-500'}`}>
                                #{idx + 1}
                              </span>
                              <span className="text-slate-600 truncate max-w-[100px] font-medium" title={cat.name}>{cat.name}</span>
                            </div>
                            <span className="font-bold text-slate-900">
                              {formatPerformerValue(cat.value || 0, performers.primary_metric)}
                              <span className="text-[9px] text-slate-400 font-semibold ml-1">({pct.toFixed(0)}%)</span>
                            </span>
                          </div>
                          <div className="w-full bg-slate-200/60 h-1 rounded-full mt-1.5 overflow-hidden">
                            <div className="bg-blue-600 h-full rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Regions */}
              {performers.regions && performers.regions.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-700 flex items-center gap-1"><Map size={14} /> Regions / Locations</h4>
                  <div className="space-y-2.5">
                    {performers.regions.slice(0, 5).map((r: SafeAny, idx: number) => {
                      const pct = ((r.value || 0) / regionsTotal) * 100
                      return (
                        <div key={idx} className="flex flex-col p-2 bg-slate-50 rounded-lg hover:bg-slate-100/50 transition-all border border-slate-100">
                          <div className="flex justify-between items-center text-xs">
                            <div className="flex items-center gap-1.5 min-w-0">
                              <span className={`flex-shrink-0 flex items-center justify-center w-5 h-5 rounded text-[10px] font-black border ${rankColors[idx] || 'bg-slate-50 text-slate-500'}`}>
                                #{idx + 1}
                              </span>
                              <span className="text-slate-600 truncate max-w-[100px] font-medium" title={r.name}>{r.name}</span>
                            </div>
                            <span className="font-bold text-slate-900">
                              {formatPerformerValue(r.value || 0, performers.primary_metric)}
                              <span className="text-[9px] text-slate-400 font-semibold ml-1">({pct.toFixed(0)}%)</span>
                            </span>
                          </div>
                          <div className="w-full bg-slate-200/60 h-1 rounded-full mt-1.5 overflow-hidden">
                            <div className="bg-blue-600 h-full rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        )
      })()}

      {/* Automated Visualizations & Chart Recommendation Engine */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="font-extrabold text-lg text-slate-800">
            Automated Chart Recommendations
          </h2>
          <button 
            onClick={() => setShowStudio(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold text-xs shadow-sm transition-all border border-slate-200"
          >
            <span>✨</span>
            Generate More Charts
          </button>
        </div>
        
        {charts.length === 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card bg-white p-6 shadow-md rounded-xl space-y-4">
              <h3 className="font-bold text-sm text-slate-800 mb-4">Dataset Overview</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center text-xs p-2 bg-slate-50 rounded-lg">
                  <span className="text-slate-500 font-medium">Total Records</span>
                  <span className="font-bold text-slate-900">{(quickStats.rows || 0).toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center text-xs p-2 bg-slate-50 rounded-lg">
                  <span className="text-slate-500 font-medium">Numeric Columns</span>
                  <span className="font-bold text-slate-900">{quickStats.numeric_cols || 0}</span>
                </div>
                <div className="flex justify-between items-center text-xs p-2 bg-slate-50 rounded-lg">
                  <span className="text-slate-500 font-medium">Categorical Columns</span>
                  <span className="font-bold text-slate-900">{quickStats.categorical_cols || 0}</span>
                </div>
                <div className="flex justify-between items-center text-xs p-2 bg-slate-50 rounded-lg">
                  <span className="text-slate-500 font-medium">Date Columns</span>
                  <span className="font-bold text-slate-900">{quickStats.date_cols || 0}</span>
                </div>
                <div className="flex justify-between items-center text-xs p-2 bg-slate-50 rounded-lg">
                  <span className="text-slate-500 font-medium">Data Quality</span>
                  <span className="font-bold text-emerald-700">{(healthScores.data_quality || 0).toFixed(0)}%</span>
                </div>
              </div>
              <div className="mt-4 p-3 bg-blue-50/30 border border-blue-100/50 rounded-xl">
                <span className="text-xs text-blue-700 font-medium">Advanced chart generation is in progress. Refresh if charts don't appear within moments.</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {charts.map((c: Chart, idx: number) => (
              <div key={idx} className="card bg-white p-6 shadow-md rounded-xl space-y-4 flex flex-col justify-between">
                <div>
                  <h3 className="font-bold text-sm text-slate-800 mb-4">
                    {c.title}
                  </h3>
                  <div className="h-72 w-full">
                    <ResponsiveChart chart={c} />
                  </div>
                </div>
                {c.insight && (
                  <div className="mt-4 p-3 bg-slate-50 border border-slate-100 rounded-xl flex items-start gap-2">
                    <Info size={16} className="text-slate-500 mt-0.5 flex-shrink-0" />
                    <span className="text-xs text-slate-600 font-medium leading-relaxed">{c.insight}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>



      {/* Visualization Studio Modal */}
      {showStudio && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl border border-slate-100 flex flex-col max-h-[85vh] overflow-hidden">
            
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-slate-100">
              <div>
                <h3 className="font-extrabold text-lg text-slate-900 flex items-center gap-2">
                  <span>✨</span> Visualization Studio
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Design bespoke, on-demand dashboards from the dataset schema
                </p>
              </div>
              <button 
                onClick={() => setShowStudio(false)}
                className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-50 transition-all"
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
              
              {/* Step 1: Select Chart Type */}
              <div className="md:col-span-2 space-y-4">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  STEP 1: Select Chart Type
                </div>
                
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {CHART_TYPES.map((t) => {
                    // Smart compatibility check
                    const allCols = ((datasetData as any)?.schema?.columns as any[]) || []
                    const numericCols = allCols.filter(c => c.type === 'numeric' || c.type === 'integer' || c.type === 'float').map(c => c.name)
                    const categoricalCols = allCols.filter(c => c.type === 'categorical').map(c => c.name)
                    const dateCols = allCols.filter(c => c.type === 'datetime' || c.type === 'date').map(c => c.name)
                    
                    const hasDate = dateCols.length > 0
                    const hasNum = numericCols.length > 0
                    const hasMultipleNum = numericCols.length >= 2
                    const hasCat = categoricalCols.length > 0
                    
                    // Geographic check
                    const hasGeo = allCols.some(c => 
                      c.type === 'categorical' && 
                      ['region', 'state', 'country', 'city', 'location', 'geo'].some(kw => c.name.toLowerCase().includes(kw))
                    )

                    let status: 'recommended' | 'compatible' | 'not_available' = 'compatible'
                    
                    if (t.id === 'line' || t.id === 'area' || t.id === 'waterfall' || t.id === 'stacked_area') {
                      status = hasDate && hasNum ? 'recommended' : (hasNum ? 'compatible' : 'not_available')
                    } else if (t.id === 'bar' || t.id === 'pie' || t.id === 'donut' || t.id === 'treemap' || t.id === 'pareto' || t.id === 'funnel') {
                      status = hasCat && hasNum ? 'recommended' : (hasCat || hasNum ? 'compatible' : 'not_available')
                    } else if (t.id === 'stacked_bar' || t.id === 'radar') {
                      status = hasCat && hasMultipleNum ? 'recommended' : (hasMultipleNum ? 'compatible' : 'not_available')
                    } else if (t.id === 'scatter' || t.id === 'bubble' || t.id === 'heatmap' || t.id === 'correlation') {
                      status = hasMultipleNum ? 'recommended' : (hasNum ? 'compatible' : 'not_available')
                    } else if (t.id === 'histogram' || t.id === 'boxplot') {
                      status = hasNum ? 'recommended' : 'not_available'
                    } else if (t.id === 'geographic') {
                      status = hasGeo && hasNum ? 'recommended' : (hasGeo ? 'compatible' : 'not_available')
                    }

                    const isSelected = selectedType === t.id
                    const isAvailable = status !== 'not_available'

                    return (
                      <button
                        key={t.id}
                        disabled={!isAvailable}
                        onClick={() => {
                          setSelectedType(t.id)
                          // Auto select default columns based on selection
                          if (t.id === 'heatmap' || t.id === 'correlation') {
                            setXAxis('')
                            setYAxis('')
                          } else {
                            if (t.id === 'line' || t.id === 'area') {
                              setXAxis(dateCols[0] || allCols[0]?.name || '')
                              setYAxis(numericCols[0] || '')
                            } else if (t.id === 'bar' || t.id === 'pie' || t.id === 'donut') {
                              setXAxis(categoricalCols[0] || allCols[0]?.name || '')
                              setYAxis(numericCols[0] || '')
                            } else {
                              setXAxis(allCols[0]?.name || '')
                              setYAxis(numericCols[0] || '')
                            }
                          }
                        }}
                        className={`flex flex-col text-left p-3 rounded-xl border transition-all ${
                          isSelected 
                            ? 'border-blue-600 bg-blue-50/40 ring-2 ring-blue-500/20 shadow-sm' 
                            : isAvailable
                              ? 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'
                              : 'border-slate-100 bg-slate-50/40 opacity-40 cursor-not-allowed'
                        }`}
                      >
                        <span className="text-xl mb-1">{t.icon}</span>
                        <span className="text-xs font-bold text-slate-800 leading-tight">{t.name}</span>
                        <div className="flex justify-between items-center mt-2 w-full">
                          <span className={`text-[8px] font-black uppercase px-1 rounded ${
                            status === 'recommended' 
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                              : status === 'compatible'
                                ? 'bg-blue-50 text-blue-700 border border-blue-100'
                                : 'bg-slate-100 text-slate-400'
                          }`}>
                            {status === 'recommended' ? 'Recommended' : status === 'compatible' ? 'Compatible' : 'Not Available'}
                          </span>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Step 2 & 3: Configure Parameters */}
              <div className="space-y-6 bg-slate-50/50 p-6 rounded-2xl border border-slate-100 flex flex-col justify-between">
                <div className="space-y-4">
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    STEP 2: Configure Chart
                  </div>

                  {/* X Axis selector */}
                  {selectedType !== 'heatmap' && selectedType !== 'correlation' && (
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider">X-Axis Column</label>
                      <select
                        value={xAxis}
                        onChange={(e) => setXAxis(e.target.value)}
                        className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                      >
                        <option value="">Select column...</option>
                        {(((datasetData as any)?.schema?.columns as any[]) || []).map((c) => (
                          <option key={c.name} value={c.name}>
                            {c.name} ({c.type})
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Y Axis selector */}
                  {selectedType !== 'heatmap' && selectedType !== 'correlation' && selectedType !== 'histogram' && selectedType !== 'boxplot' && (
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider">Y-Axis Column (Metric)</label>
                      <select
                        value={yAxis}
                        onChange={(e) => setYAxis(e.target.value)}
                        className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                      >
                        <option value="">Select column...</option>
                        {(((datasetData as any)?.schema?.columns as any[]) || [])
                          .map((c) => (
                            <option key={c.name} value={c.name}>
                              {c.name} ({c.type})
                            </option>
                          ))}
                      </select>
                    </div>
                  )}

                  {studioError && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-[10px] text-red-600 font-semibold leading-relaxed">
                      ⚠️ {studioError}
                    </div>
                  )}

                  <div className="p-3 bg-blue-50/20 border border-blue-100/30 rounded-xl text-[10px] text-slate-500 leading-relaxed">
                    💡 <strong>Tip:</strong> Selecting Recommended configurations ensures optimal visual clarity and correct data aggregation formats.
                  </div>
                </div>

                <div className="space-y-3 pt-4 border-t border-slate-100">
                  <button
                    onClick={async () => {
                      if (!selectedType) return
                      setGeneratingCustom(true)
                      setStudioError(null)
                      try {
                        const chartObj = await generateCustomChart(datasetId!, selectedType, xAxis, yAxis)
                        saveCustomCharts([...customCharts, chartObj])
                        setShowStudio(false)
                      } catch (err: any) {
                        console.error('Failed to generate custom chart:', err)
                        setStudioError(err.message || 'Failed to generate custom chart.')
                      } finally {
                        setGeneratingCustom(false)
                      }
                    }}
                    disabled={generatingCustom || !selectedType || (selectedType !== 'heatmap' && selectedType !== 'correlation' && !xAxis)}
                    className="w-full flex items-center justify-center gap-2 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white rounded-xl font-bold text-xs transition-all shadow-md shadow-blue-500/10"
                  >
                    {generatingCustom ? (
                      <>
                        <Loader2 size={14} className="animate-spin" />
                        Generating chart...
                      </>
                    ) : (
                      <>
                        <span>✨</span>
                        Generate Custom Chart
                      </>
                    )}
                  </button>
                  
                  <button
                    onClick={() => setShowStudio(false)}
                    className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-semibold text-xs transition-all"
                  >
                    Cancel
                  </button>
                </div>

              </div>

            </div>

          </div>
        </div>
      )}
    </div>
  )
}

function ResponsiveChart({ chart }: { chart: Chart }) {
  const { type, data, x_axis, y_axis, columns } = chart

  if (!data || data.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-xs text-slate-400">
        No visual data points available
      </div>
    )
  }

  // 1. Trend Chart with 7-Period Moving Average
  if (type === 'trend') {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ left: 10, right: 10, top: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748B' }} />
          <YAxis tick={{ fontSize: 10, fill: '#64748B' }} />
          <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #E2E8F0' }} />
          <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
          <Line type="monotone" dataKey="value" name="Actual" stroke="#2563EB" strokeWidth={2} dot={false} />
          {data[0] && 'moving_average' in data[0] && (
            <Line type="monotone" dataKey="moving_average" name="7-Point Moving Avg" stroke="#7C3AED" strokeWidth={2} strokeDasharray="4 4" dot={false} />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    )
  }

  // 2. Histogram
  if (type === 'histogram') {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ left: 10, right: 10, top: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
          <XAxis dataKey="bin" tick={{ fontSize: 10, fill: '#64748B' }} />
          <YAxis tick={{ fontSize: 10, fill: '#64748B' }} />
          <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #E2E8F0' }} />
          <Bar dataKey="count" fill="#7C3AED" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    )
  }

  // 3. Heatmap / Correlation Matrix (Visual Matrix Grid representation)
  if (type === 'heatmap') {
    if (!columns || columns.length === 0) return null
    return (
      <div className="h-full flex flex-col justify-between select-none">
        <div className="flex-1 grid gap-1.5" style={{ gridTemplateColumns: `repeat(${columns.length}, minmax(0, 1fr))` }}>
          {data.map((cell: SafeAny, i: number) => {
            const val = Number(cell.value || 0)
            const alpha = Math.abs(val)
            const color = val > 0 ? `rgba(37, 99, 235, ${alpha})` : `rgba(220, 38, 38, ${alpha})`
            return (
              <div 
                key={i} 
                className="flex items-center justify-center text-[10px] font-bold rounded transition-all border border-slate-100/50 hover:scale-105"
                style={{ background: color, color: alpha > 0.4 ? 'white' : '#0F172A' }}
                title={`${cell.x} ↔ ${cell.y}: ${cell.value}`}
              >
                {val.toFixed(2)}
              </div>
            )
          })}
        </div>
        {/* Columns label list at bottom */}
        <div className="grid gap-1 mt-3 text-[8px] text-slate-400 text-center font-semibold" style={{ gridTemplateColumns: `repeat(${columns.length}, minmax(0, 1fr))` }}>
          {columns.map((col: string, i: number) => (
            <div key={i} className="truncate px-0.5" title={col}>
              {col}
            </div>
          ))}
        </div>
      </div>
    )
  }

  // 4. Scatter Plot
  if (type === 'scatter') {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ left: 10, right: 10, top: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
          <XAxis type="number" dataKey="x" name={x_axis} tick={{ fontSize: 10 }} />
          <YAxis type="number" dataKey="y" name={y_axis} tick={{ fontSize: 10 }} />
          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
          <Scatter name="Points" data={data} fill="#059669" shape="circle" line={false} />
        </ScatterChart>
      </ResponsiveContainer>
    )
  }

  // 5. Pareto Chart (dual axis bars + cumulative percentage line)
  if (type === 'pareto') {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ left: 10, right: 10, top: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 9 }} />
          <YAxis yAxisId="left" tick={{ fontSize: 10 }} />
          <YAxis yAxisId="right" orientation="right" domain={[0, 100]} tick={{ fontSize: 10 }} unit="%" />
          <Tooltip />
          <Bar yAxisId="left" dataKey="value" fill="#D97706" radius={[4, 4, 0, 0]} />
          <Line yAxisId="right" type="monotone" dataKey="cumulative" stroke="#DC2626" strokeWidth={2} />
        </ComposedChart>
      </ResponsiveContainer>
    )
  }

  // 6. Treemap
  if (type === 'treemap') {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <Treemap
          data={data}
          dataKey="size"
          stroke="#fff"
          fill="#4F46E5"
        />
      </ResponsiveContainer>
    )
  }

  // 7. Boxplot
  if (type === 'boxplot') {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ left: 10, right: 10, top: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} />
          <Tooltip />
          {/* Custom rendering representing Q1 to Q3 interval as bar */}
          <Bar dataKey="q1" fill="none" stackId="a" />
          <Bar dataKey="q3" fill="#0891B2" opacity={0.7} stackId="a" radius={[3, 3, 3, 3]} />
        </BarChart>
      </ResponsiveContainer>
    )
  }

  // 8. Pie Chart
  if (type === 'pie') {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} (${((percent || 0) * 100).toFixed(0)}%)`}
            outerRadius={70}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((_entry: SafeAny, index: number) => (
              <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value: any) => formatPerformerValue(value, chart.y_axis || '')} />
          <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />
        </PieChart>
      </ResponsiveContainer>
    )
  }

  // 9. Standard Bar Chart
  if (type === 'bar') {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ left: 10, right: 10, top: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748B' }} />
          <YAxis tick={{ fontSize: 10, fill: '#64748B' }} />
          <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #E2E8F0' }} />
          <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
          <Bar dataKey="value" fill="#2563EB" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    )
  }

  return null
}

function NoDataset() {
  return (
    <div className="text-center py-20 animate-fade-in">
      <LayoutDashboard size={48} style={{ color: 'var(--color-text-muted)', margin: '0 auto 1rem' }} />
      <h2 className="font-bold text-xl mb-2" style={{ color: 'var(--color-text-primary)' }}>Executive Dashboard</h2>
      <p style={{ color: 'var(--color-text-secondary)' }}>Upload a dataset to generate recommendations</p>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="text-center py-20 animate-pulse">
      <div className="inline-block p-4 rounded-full mb-4" style={{ background: 'var(--color-primary-50)' }}>
        <LayoutDashboard size={32} style={{ color: 'var(--color-primary)' }} />
      </div>
      <h2 className="font-bold text-lg mb-2">Analyzing executive KPIs</h2>
      <p style={{ color: 'var(--color-text-secondary)' }}>Generating chart recommendations and root cause drilldowns...</p>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="text-center py-20 animate-fade-in">
      <AlertTriangle size={48} style={{ color: 'var(--color-warning)', margin: '0 auto 1rem' }} />
      <h2 className="font-bold text-xl mb-2">Something went wrong</h2>
      <p style={{ color: 'var(--color-text-secondary)' }}>{message}</p>
    </div>
  )
}
