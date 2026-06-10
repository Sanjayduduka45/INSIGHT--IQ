/**
 * InsightIQ — Customer Intelligence Dashboard
 */

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getCustomerIntelligence, getDataset, getCharts, generateCustomChart, getDatasetPreview } from '../lib/api'
import { 
  Users, Award, TrendingUp, BarChart3, 
  UsersRound, FileText, Heart, X, Loader2, Info,
  Edit2, Save, FileSpreadsheet, PinOff, AlertTriangle
} from 'lucide-react'
import { 
  BarChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ScatterChart, Scatter, ComposedChart, Treemap,
  PieChart, Pie, Cell
} from 'recharts'
import type { SafeAny, Chart } from '../types'
import { formatCurrency, formatCompactNumber, formatPercent } from '../lib/formatters'

const CHART_COLORS = ['#2563EB', '#7C3AED', '#059669', '#D97706', '#DC2626', '#0891B2', '#4F46E5', '#EA580C']
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

const rankColors = [
  'bg-amber-100 text-amber-800 border-amber-200', 
  'bg-slate-100 text-slate-800 border-slate-200', 
  'bg-amber-700/10 text-amber-900 border-amber-700/20', 
  'bg-slate-50 text-slate-600 border-slate-100', 
  'bg-slate-50 text-slate-600 border-slate-100'
];

interface Props {
  datasetId: string | null
}

const formatPerformerValue = (val: number, metricName: string) => {
  const normalized = (metricName || '').toLowerCase()
  const isCurrency = ['price', 'revenue', 'sales', 'cost', 'income', 'profit', 'amount', 'spend', 'budget', 'bill', 'charge', 'total_value', 'mrr', 'arr', 'ltv', 'cac', 'clv'].some(kw => normalized.includes(kw))
  if (isCurrency) {
    return formatCurrency(val)
  }
  return formatCompactNumber(val)
}

export default function CustomerIntelligence({ datasetId }: Props) {
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

  const { data, isLoading, error: customerError } = useQuery({
    queryKey: ['customer-intelligence', datasetId],
    queryFn: () => getCustomerIntelligence(datasetId!),
    enabled: !!datasetId,
  })

  const { data: datasetData } = useQuery({
    queryKey: ['dataset', datasetId],
    queryFn: () => getDataset(datasetId!),
    enabled: !!datasetId,
  })

  const { data: chartsData, isLoading: chartsLoading, error: chartsError } = useQuery({
    queryKey: ['charts-customer', datasetId],
    queryFn: async () => {
      try {
        return await getCharts(datasetId!, 'customer')
      } catch (err) {
        console.warn('Customer charts query failed. Building from preview data.', err)
        try {
          const preview = await getDatasetPreview(datasetId!) as any
          const columns = preview.columns || []
          const rows = preview.rows || []
          const numCols = columns.filter((c: any) => c.type === 'numeric' || c.type === 'integer' || c.type === 'float')
          const catCols = columns.filter((c: any) => c.type === 'categorical')
          const fallbackCharts: any[] = []
          if (catCols.length > 0 && numCols.length > 0 && rows.length > 0) {
            const catName = catCols[0].name
            const metricName = numCols[0].name
            const grouped: Record<string, number> = {}
            rows.forEach((r: any) => {
              const key = String(r[catName] || 'Unknown')
              grouped[key] = (grouped[key] || 0) + (Number(r[metricName]) || 0)
            })
            const sorted = Object.entries(grouped).sort((a, b) => b[1] - a[1]).slice(0, 8)
            fallbackCharts.push({
              type: 'bar',
              title: `${metricName} by ${catName}`,
              x_axis: catName, y_axis: metricName,
              insight: `Live preview: ${metricName} aggregated by ${catName}.`,
              data: sorted.map(([name, value]) => ({ name, value: Math.round(value) }))
            })
          }
          if (catCols.length > 0 && rows.length > 0) {
            const catName = catCols[0].name
            const counts: Record<string, number> = {}
            rows.forEach((r: any) => { const v = String(r[catName] || 'Unknown'); counts[v] = (counts[v] || 0) + 1 })
            const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 8)
            fallbackCharts.push({
              type: 'bar',
              title: `Record Count by ${catName}`,
              x_axis: catName, y_axis: 'Records',
              insight: `Live preview: record distribution across ${catName}.`,
              data: sorted.map(([name, value]) => ({ name, value }))
            })
          }
          fallbackCharts.push({
            type: 'bar',
            title: 'Column Completeness',
            x_axis: 'Column', y_axis: 'Non-Null Records',
            insight: 'Data completeness from live preview.',
            data: columns.slice(0, 8).map((c: any) => ({
              name: c.name.length > 15 ? c.name.substring(0, 15) : c.name,
              value: rows.filter((r: any) => r[c.name] != null && r[c.name] !== '').length
            }))
          })
          return { charts: fallbackCharts }
        } catch { /* preview failed */ }
        return { charts: [] }
      }
    },
    enabled: !!datasetId,
  })

  const error = customerError || chartsError
  if (!datasetId) return <NoDataset />
  if (isLoading || chartsLoading) return <LoadingState />
  if (error) {
    return (
      <div className="text-center py-20 animate-fade-in">
        <AlertTriangle size={48} style={{ color: 'var(--color-warning)', margin: '0 auto 1rem' }} />
        <h2 className="font-bold text-xl mb-2">Something went wrong</h2>
        <p style={{ color: 'var(--color-text-secondary)' }}>{(error as Error).message || 'Failed to load Customer Intelligence.'}</p>
      </div>
    )
  }
  if (!data) return null

  if (!data.eligible) {
    return (
      <div className="animate-fade-in max-w-xl mx-auto py-20 text-center space-y-6">
        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto text-slate-400">
          <Users size={32} />
        </div>
        <h2 className="text-xl font-bold text-slate-900">Customer Intelligence Not Available</h2>
        <p className="text-sm text-slate-500 leading-relaxed">
          {data.message}
        </p>
        <div className="p-4 bg-slate-50 border border-slate-100 rounded-xl text-xs text-slate-400 text-left">
          <strong>Setup Heuristics:</strong> Make sure your file contains a column with name tokens like 'customer', 'cust', 'client', or 'buyer' alongside a metric containing 'revenue', 'sales', 'spend', or 'total'.
        </div>
      </div>
    )
  }

  const defaultCharts = chartsData?.charts || []

  return (
    <div className="animate-fade-in space-y-8">
      {/* Header */}
      <div className="page-header flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <UsersRound className="text-indigo-600" />
            Customer Intelligence Hub
          </h1>
          <p className="page-subtitle">
            RFM segments (Champions, Loyal, At Risk, Lost), Customer Lifetime Value (CLV), and Pareto distribution
          </p>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="kpi-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[10px] font-bold uppercase tracking-wider">Total Active Customers</span>
            <Users size={16} className="text-blue-500" />
          </div>
          <div className="text-2xl font-black text-slate-900">{formatCompactNumber(data.total_customers)}</div>
          <div className="text-[9px] text-slate-400 mt-1 truncate">Unique customer entities binned</div>
        </div>

        <div className="kpi-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[10px] font-bold uppercase tracking-wider">Repeat Buyer Rate</span>
            <Heart size={16} className="text-rose-500" />
          </div>
          <div className="text-2xl font-black text-slate-900">{formatPercent(data.repeat_rate, false)}</div>
          <div className="text-[9px] text-slate-400 mt-1 truncate">
            {formatCompactNumber(data.repeat_count)} repeat accounts ({formatPercent(data.repeat_revenue_share, false)} of sales)
          </div>
        </div>

        <div className="kpi-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[10px] font-bold uppercase tracking-wider">Pareto 80/20 Index</span>
            <Award size={16} className="text-purple-500" />
          </div>
          <div className="text-2xl font-black text-slate-900">{formatPercent(data.pareto_80_20_customer_pct, false)}</div>
          <div className="text-[9px] text-slate-400 mt-1 truncate">
            Top {formatPercent(data.pareto_80_20_customer_pct, false)} of customers generate 80% of revenue
          </div>
        </div>

        <div className="kpi-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[10px] font-bold uppercase tracking-wider">Top 20% Spend Share</span>
            <TrendingUp size={16} className="text-emerald-500" />
          </div>
          <div className="text-2xl font-black text-slate-900">{formatPercent(data.pareto_20_concentration, false)}</div>
          <div className="text-[9px] text-slate-400 mt-1 truncate">Total revenue share of top 20%</div>
        </div>
      </div>

      {/* Pinned Custom Visualizations Section */}
      {customCharts.length > 0 && (
        <div className="space-y-4 pt-8 border-t border-slate-100 mb-8 animate-fade-in">
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

      {/* Recommended Business Charts Grid */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="font-extrabold text-lg text-slate-800 flex items-center gap-2">
            <BarChart3 size={20} className="text-blue-500" />
            Recommended Customer Intelligence Charts
          </h2>
          <button 
            onClick={() => setShowStudio(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold text-xs shadow-sm transition-all border border-slate-200"
          >
            <span>✨</span>
            Generate More Charts
          </button>
        </div>

        {defaultCharts.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {defaultCharts.map((c: Chart, idx: number) => (
              <div key={idx} className="card bg-white p-6 shadow-md rounded-xl space-y-4 flex flex-col justify-between">
                <div>
                  <h3 className="font-bold text-sm text-slate-800 mb-4 flex items-center gap-2">
                    {c.title}
                  </h3>
                  <div className="h-64 w-full">
                    <ResponsiveChart chart={c} />
                  </div>
                  {c.title.includes("RFM Segments") && data.segments && (
                    <div className="space-y-2 mt-4 border-t pt-4 border-slate-100 max-h-48 overflow-y-auto">
                      {Object.entries(data.segments).map(([key, seg]: [string, any], sIdx: number) => (
                        <div key={key} className="flex justify-between items-center text-[10px]">
                          <span className="flex items-center gap-1.5 text-slate-500">
                            <span className="w-2 h-2 rounded-full" style={{ background: CHART_COLORS[sIdx % CHART_COLORS.length] }} />
                            {seg.name} ({formatCompactNumber(seg.customer_count)})
                          </span>
                          <span className="font-semibold text-slate-900">
                            {formatCurrency(seg.total_spend)} ({formatPercent(seg.share_percentage, false)})
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
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
        ) : (
          <div className="p-6 bg-slate-50 rounded-xl text-center text-xs text-slate-500">
            No recommended charts available for this dataset schema.
          </div>
        )}
      </div>



      {/* Customer Segments Profile Directory */}
      <div className="card card-body shadow-sm">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-1.5">
          <Award size={16} className="text-yellow-500" />
          Top Customer Segment Profiling Directory
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left min-w-[700px]">
            <thead>
              <tr className="border-b text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-2.5">Rank</th>
                <th className="py-2.5">Customer Identity</th>
                <th className="py-2.5">RFM Segment</th>
                <th className="py-2.5">Total Spend & Share</th>
                <th className="py-2.5">Orders</th>
                <th className="py-2.5">Churn Risk</th>
                <th className="py-2.5">Est. CLV</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.top_customers.map((c: any) => (
                <tr key={c.rank} className="hover:bg-slate-50/50">
                  <td className="py-3">
                    <span className={`inline-flex items-center justify-center w-6 h-6 rounded-lg text-[10px] font-black border ${rankColors[c.rank - 1] || 'bg-slate-50 text-slate-500 border-slate-200'}`}>
                      #{c.rank}
                    </span>
                  </td>
                  <td className="py-3 font-bold text-slate-900 truncate max-w-[120px]">{c.customer}</td>
                  <td className="py-3">
                    <span className="px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider"
                          style={{
                            background: c.segment === 'Champions' ? '#E0F2FE' : c.segment === 'Loyal Customers' ? '#D1FAE5' : c.segment === 'At Risk' ? '#FEF3C7' : c.segment === 'Lost Customers' ? '#FEE2E2' : '#F1F5F9',
                            color: c.segment === 'Champions' ? '#0369A1' : c.segment === 'Loyal Customers' ? '#047857' : c.segment === 'At Risk' ? '#B45309' : c.segment === 'Lost Customers' ? '#B91C1C' : '#475569'
                          }}>
                      {c.segment}
                    </span>
                  </td>
                  <td className="py-3">
                    <div className="font-semibold text-slate-800">{formatCurrency(c.spend)}</div>
                    <div className="flex items-center gap-1.5 mt-1">
                      <div className="w-16 bg-slate-200/60 h-1 rounded-full overflow-hidden">
                        <div className="bg-blue-600 h-full rounded-full" style={{ width: `${c.share}%` }} />
                      </div>
                      <span className="text-[9px] text-slate-400 font-semibold">{c.share}%</span>
                    </div>
                  </td>
                  <td className="py-3 text-slate-600 font-medium">{c.transactions}</td>
                  <td className="py-3">
                    <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full"
                            style={{ background: c.churn_risk > 70 ? '#EF4444' : c.churn_risk > 40 ? '#F59E0B' : '#10B981' }} />
                      <span className="font-semibold text-slate-700">{c.churn_risk}%</span>
                    </div>
                  </td>
                  <td className="py-3 font-bold text-slate-900">{formatCurrency(c.clv)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Segment Insights Card */}
      {data.insights && data.insights.length > 0 && (
        <div className="card card-body shadow-sm">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <FileText size={16} className="text-indigo-600" />
            Strategic Customer Intelligence Insights
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {data.insights.map((ins: string, idx: number) => (
              <div key={idx} className="p-3 bg-indigo-50/20 border border-indigo-100/30 rounded-xl text-xs text-slate-600 leading-relaxed font-medium">
                {ins}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Visualization Studio Modal */}
      {showStudio && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in text-left">
          <div className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl border border-slate-100 flex flex-col max-h-[85vh] overflow-hidden text-slate-700">
            
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
                    const allCols = ((datasetData as any)?.schema?.columns as any[]) || []
                    const numericCols = allCols.filter(c => c.type === 'numeric' || c.type === 'integer' || c.type === 'float').map(c => c.name)
                    const categoricalCols = allCols.filter(c => c.type === 'categorical').map(c => c.name)
                    const dateCols = allCols.filter(c => c.type === 'datetime' || c.type === 'date').map(c => c.name)
                    
                    const hasDate = dateCols.length > 0
                    const hasNum = numericCols.length > 0
                    const hasMultipleNum = numericCols.length >= 2
                    const hasCat = categoricalCols.length > 0
                    
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
            <Line type="monotone" dataKey="moving_average" name="Moving Average" stroke="#7C3AED" strokeWidth={2} strokeDasharray="4 4" dot={false} />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    )
  }

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

  if (type === 'boxplot') {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ left: 10, right: 10, top: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} />
          <Tooltip />
          <Bar dataKey="q1" fill="none" stackId="a" />
          <Bar dataKey="q3" fill="#0891B2" opacity={0.7} stackId="a" radius={[3, 3, 3, 3]} />
        </BarChart>
      </ResponsiveContainer>
    )
  }

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

  if (type === 'bar') {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ left: 10, right: 10, top: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748B' }} />
          <YAxis tick={{ fontSize: 10, fill: '#64748B' }} />
          <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #E2E8F0' }} />
          <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
          <Bar dataKey="value" fill="#2563EB" radius={[4, 4, 0, 0]}>
            {data.map((_entry: SafeAny, index: number) => (
              <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    )
  }

  return null
}

function NoDataset() {
  return (
    <div className="text-center py-20 animate-fade-in card bg-white border border-slate-200 rounded-2xl shadow-sm">
      <Users size={48} className="text-slate-300 mx-auto mb-3" />
      <h2 className="font-extrabold text-lg text-slate-900 mb-1">Customer Intelligence</h2>
      <p className="text-xs text-slate-400">Please upload a valid dataset to run RFM segmentations and CLV forecasts.</p>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="text-center py-20 animate-pulse space-y-4">
      <div className="w-12 h-12 bg-indigo-50 text-indigo-500 rounded-full flex items-center justify-center mx-auto">
        <UsersRound size={24} />
      </div>
      <div>
        <h2 className="font-extrabold text-base text-slate-800">Calculating Customer RFM Matrices</h2>
        <p className="text-xs text-slate-400">Attributing loyalty segments, lifetime value models, and churn risk variables...</p>
      </div>
    </div>
  )
}
