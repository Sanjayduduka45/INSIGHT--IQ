import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getOverview } from '../lib/api'
import type { Chart, KPI, SafeAny } from '../types'
import { 
  TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight, Minus, 
  AlertTriangle, Lightbulb, Users, Package, Map, Layers, LayoutDashboard,
  ShieldAlert, Database, Hash, FileText, CheckCircle, X, Download, Loader2, Info
} from 'lucide-react'
import { 
  BarChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ScatterChart, Scatter, ComposedChart, Treemap
} from 'recharts'

interface Props {
  datasetId: string | null
}

const formatPerformerValue = (val: number, metricName: string) => {
  const normalized = (metricName || '').toLowerCase()
  const isCurrency = ['price', 'revenue', 'sales', 'cost', 'income', 'profit', 'amount', 'spend', 'budget', 'bill', 'charge', 'total_value', 'mrr', 'arr', 'ltv', 'cac'].some(kw => normalized.includes(kw))
  if (isCurrency) {
    return `$${val.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
  }
  return val.toLocaleString(undefined, { maximumFractionDigits: 0 })
}

export default function ExecutiveDashboard({ datasetId }: Props) {
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['overview', datasetId],
    queryFn: () => getOverview(datasetId!),
    enabled: !!datasetId,
  })

  const { data: chartsData, isLoading: chartsLoading } = useQuery({
    queryKey: ['charts', datasetId],
    queryFn: async () => {
      const res = await fetch(`/api/analytics/${datasetId}/charts`)
      if (!res.ok) throw new Error('Failed to fetch charts')
      return res.json()
    },
    enabled: !!datasetId,
  })

  const { data: rootCauseData, isLoading: rootCauseLoading } = useQuery({
    queryKey: ['root-cause', datasetId],
    queryFn: async () => {
      const res = await fetch(`/api/analytics/${datasetId}/root-cause`)
      if (!res.ok) throw new Error('Failed to fetch root cause')
      return res.json()
    },
    enabled: !!datasetId,
  })

  const [showHealth, setShowHealth] = useState(false)
  const [exporting, setExporting] = useState<'pdf' | 'ppt' | null>(null)

  if (!datasetId) return <NoDataset />
  if (overviewLoading || chartsLoading || rootCauseLoading) return <LoadingState />
  if (!overview) return null

  const growth = (overview.growth && typeof overview.growth === 'object' && 'growth_rate' in overview.growth)
    ? (overview.growth as { growth_rate: number; status: string })
    : { growth_rate: 0, status: 'stable' }
  const performers = overview.performers || {}
  const charts = chartsData?.charts || []
  const healthScores = overview.health_scores || {}
  const quickStats = overview.quick_stats || {}
  const summaryFields = overview.executive_intelligence?.summary_fields || {}

  const handleExport = async (format: 'pdf' | 'ppt') => {
    setExporting(format)
    try {
      const token = localStorage.getItem('insightiq_token')
      const headers: Record<string, string> = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      const res = await fetch(`/api/export/${datasetId}/${format}`, { headers })
      if (!res.ok) throw new Error('Export failed')
      
      const blob = await res.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `InsightIQ_Executive_Report_${overview.dataset_name || 'Report'}.${format === 'pdf' ? 'pdf' : 'pptx'}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(downloadUrl)
    } catch (err) {
      console.error(err)
      alert(`Failed to export ${format.toUpperCase()} report.`)
    } finally {
      setExporting(null)
    }
  }

  return (
    <div className="animate-fade-in space-y-8">
      {/* Page Header */}
      <div className="page-header flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <LayoutDashboard className="text-blue-600" />
            Executive Command Center
          </h1>
          <p className="page-subtitle">
            Enterprise intelligence, health score breakdowns, and diagnostic variance root causes
          </p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          {/* Primary growth index */}
          <div className="flex items-center gap-4 bg-white px-4 py-2 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
              Primary growth index
            </div>
            <div className="flex items-center gap-1 font-extrabold text-base"
                 style={{ color: growth.growth_rate > 0 ? 'var(--color-success)' : growth.growth_rate < 0 ? 'var(--color-danger)' : 'var(--color-text-secondary)' }}>
              {growth.growth_rate > 0 ? <ArrowUpRight size={18} /> : growth.growth_rate < 0 ? <ArrowDownRight size={18} /> : <Minus size={18} />}
              {growth.growth_rate > 0 ? '+' : ''}{growth.growth_rate.toFixed(1)}%
            </div>
          </div>

          {/* Export Buttons */}
          <button 
            onClick={() => handleExport('pdf')}
            disabled={exporting !== null}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold text-sm shadow-sm transition-all disabled:opacity-50"
          >
            {exporting === 'pdf' ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            Export PDF Report
          </button>
          <button 
            onClick={() => handleExport('ppt')}
            disabled={exporting !== null}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl font-semibold text-sm shadow-sm transition-all disabled:opacity-50"
          >
            {exporting === 'ppt' ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            Export PowerPoint
          </button>
        </div>
      </div>

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
              <p className="text-slate-800 text-sm leading-relaxed font-medium bg-slate-50 p-4 rounded-xl border border-slate-100">
                {overview.executive_intelligence.summary}
              </p>
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

      {/* Risks & Opportunities and Root Cause Diagnostics Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Root Cause Drilldown Engine */}
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
            {rootCauseData?.root_causes?.map((rc: any, idx: number) => {
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
                        <p className="text-xs text-slate-400 italic">No significant drivers detected.</p>
                      )}
                    </div>

                    {/* Waterfall values */}
                    <div className="space-y-3">
                      <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Variance Steps</div>
                      {rc.waterfall && rc.waterfall.length > 0 ? (
                        <div className="bg-white border border-slate-200/60 rounded-lg shadow-sm overflow-hidden">
                          <table className="w-full text-xs text-left">
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
                      ) : (
                        <p className="text-xs text-slate-400 italic">No waterfall step data compiled.</p>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
            
            {(!rootCauseData?.root_causes || rootCauseData.root_causes.length === 0) && (
              <p className="text-xs text-slate-400 italic">No significant root cause analyses available for this dataset type.</p>
            )}
          </div>
        </div>

        {/* Right: Key Risks & Growth Opportunities */}
        <div className="card bg-white p-6 shadow-md rounded-xl space-y-6">
          {/* Opportunities Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-extrabold text-slate-800 flex items-center gap-1.5">
              <TrendingUp size={16} className="text-indigo-600" />
              Strategic Opportunities
            </h3>
            <div className="space-y-2.5">
              {overview.executive_intelligence?.opportunities?.map((opp: string, idx: number) => (
                <div key={idx} className="p-3 bg-indigo-50/20 border border-indigo-100/30 rounded-lg text-xs text-slate-700 leading-relaxed">
                  {opp}
                </div>
              ))}
              {(!overview.executive_intelligence?.opportunities || overview.executive_intelligence.opportunities.length === 0) && (
                <p className="text-xs text-slate-400 italic">No significant opportunities identified.</p>
              )}
            </div>
          </div>

          {/* Risks Section */}
          <div className="space-y-4 pt-4 border-t border-slate-100">
            <h3 className="text-sm font-extrabold text-slate-800 flex items-center gap-1.5">
              <ShieldAlert size={16} className="text-red-600" />
              Risks & Mitigations
            </h3>
            <div className="space-y-2.5">
              {overview.executive_intelligence?.risks?.map((risk: string, idx: number) => (
                <div key={idx} className="p-3 bg-red-50/20 border border-red-100/30 rounded-lg text-xs text-slate-700 leading-relaxed">
                  {risk}
                </div>
              ))}
              {(!overview.executive_intelligence?.risks || overview.executive_intelligence.risks.length === 0) && (
                <p className="text-xs text-slate-400 italic">No operational risks flagged.</p>
              )}
            </div>
          </div>
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
      {performers.primary_metric && (
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
                <div className="space-y-1.5">
                  {performers.products.slice(0, 5).map((p: SafeAny, idx: number) => (
                    <div key={idx} className="flex justify-between items-center text-xs p-2 bg-slate-50 rounded-lg hover:bg-slate-100/50">
                      <span className="text-slate-600 truncate max-w-[120px] font-medium">{p.name}</span>
                      <span className="font-bold text-slate-900">
                        {formatPerformerValue(p.value || 0, performers.primary_metric)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Customers */}
            {performers.customers && performers.customers.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-700 flex items-center gap-1"><Users size={14} /> Customers / Clients</h4>
                <div className="space-y-1.5">
                  {performers.customers.slice(0, 5).map((c: SafeAny, idx: number) => (
                    <div key={idx} className="flex justify-between items-center text-xs p-2 bg-slate-50 rounded-lg hover:bg-slate-100/50">
                      <span className="text-slate-600 truncate max-w-[120px] font-medium">{c.name}</span>
                      <span className="font-bold text-slate-900">
                        {formatPerformerValue(c.value || 0, performers.primary_metric)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Categories */}
            {performers.categories && performers.categories.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-700 flex items-center gap-1"><Layers size={14} /> Categories</h4>
                <div className="space-y-1.5">
                  {performers.categories.slice(0, 5).map((cat: SafeAny, idx: number) => (
                    <div key={idx} className="flex justify-between items-center text-xs p-2 bg-slate-50 rounded-lg hover:bg-slate-100/50">
                      <span className="text-slate-600 truncate max-w-[120px] font-medium">{cat.name}</span>
                      <span className="font-bold text-slate-900">
                        {formatPerformerValue(cat.value || 0, performers.primary_metric)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Regions */}
            {performers.regions && performers.regions.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-700 flex items-center gap-1"><Map size={14} /> Regions / Locations</h4>
                <div className="space-y-1.5">
                  {performers.regions.slice(0, 5).map((r: SafeAny, idx: number) => (
                    <div key={idx} className="flex justify-between items-center text-xs p-2 bg-slate-50 rounded-lg hover:bg-slate-100/50">
                      <span className="text-slate-600 truncate max-w-[120px] font-medium">{r.name}</span>
                      <span className="font-bold text-slate-900">
                        {formatPerformerValue(r.value || 0, performers.primary_metric)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Automated Visualizations & Chart Recommendation Engine */}
      <div className="space-y-4">
        <h2 className="font-extrabold text-lg text-slate-800">
          Automated Chart Recommendations
        </h2>
        {charts.length === 0 ? (
          <div className="card text-center py-12 bg-white border border-slate-200">
            <p className="text-slate-500 text-sm">Not enough matching columns to recommend advanced charts.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {charts.map((c: Chart, idx: number) => (
              <div key={idx} className="card bg-white p-6 shadow-md rounded-xl space-y-4">
                <h3 className="font-bold text-sm text-slate-800">
                  {c.title}
                </h3>
                <div className="h-72 w-full">
                  <ResponsiveChart chart={c} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
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
