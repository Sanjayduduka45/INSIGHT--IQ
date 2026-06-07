/**
 * InsightIQ — Anomaly Center
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { detectAnomalies } from '../lib/api'
import { 
  AlertTriangle, AlertCircle, Info, ShieldAlert, 
  Layers, Settings, BarChart2, Activity, HelpCircle
} from 'lucide-react'
import type { SafeAny, Anomaly } from '../types'

interface Props {
  datasetId: string | null
}

export default function AnomalyCenter({ datasetId }: Props) {
  const [contamination, setContamination] = useState(0.05)

  const { data, isLoading } = useQuery({
    queryKey: ['anomalies', datasetId, contamination],
    queryFn: () => detectAnomalies(datasetId!, contamination),
    enabled: !!datasetId,
  })

  if (!datasetId) return <NoDataset label="Anomaly Center" />

  return (
    <div className="animate-fade-in space-y-6">
      {/* Header */}
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <ShieldAlert className="text-red-500" />
            Anomaly Intelligence Center
          </h1>
          <p className="page-subtitle">Multi-model consensus anomaly detection and business impact diagnostics</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
            <Settings size={14} /> Sensitivity
          </label>
          <select 
            value={contamination} 
            onChange={e => setContamination(Number(e.target.value))}
            className="border rounded-xl px-3 py-1.5 text-xs font-semibold shadow-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
          >
            <option value={0.01}>Conservative (1% target)</option>
            <option value={0.05}>Balanced (5% target)</option>
            <option value={0.10}>Sensitive (10% target)</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <LoadingState />
      ) : data ? (
        <>
          {/* Summary Strip */}
          <div className="card border-l-4 p-4 flex items-center gap-4 shadow-sm"
               style={{ 
                 borderLeftColor: data.total_anomalies > 0 ? 'var(--color-danger)' : 'var(--color-success)',
                 background: data.total_anomalies > 0 ? 'var(--color-danger-light)' : 'var(--color-success-light)' 
               }}>
            {data.total_anomalies > 0 ? (
              <AlertTriangle size={24} className="text-red-600 flex-shrink-0" />
            ) : (
              <ShieldAlert size={24} className="text-emerald-600 flex-shrink-0" />
            )}
            <div>
              <div className="font-bold text-sm text-slate-800">
                {data.summary}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                Consensus scanning evaluates records across 5 analytical models to verify true deviations.
              </div>
            </div>
          </div>

          {/* Anomaly Dashboard Panel */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
            <div className="kpi-card flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider">Total Records Inspected</span>
                <Layers size={14} className="text-slate-400" />
              </div>
              <div className="text-2xl font-black text-slate-900">{data.total_records?.toLocaleString()}</div>
              <div className="text-[9px] text-slate-400 mt-1">Full dataset cardinality</div>
            </div>

            <div className="kpi-card flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider">Outliers Identified</span>
                <AlertTriangle size={14} className="text-amber-500" />
              </div>
              <div className="text-2xl font-black text-slate-900">{data.total_anomalies}</div>
              <div className="text-[9px] text-slate-400 mt-1">Verify severity details below</div>
            </div>

            <div className="kpi-card flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider">Anomaly Rate</span>
                <Activity size={14} className="text-rose-500" />
              </div>
              <div className="text-2xl font-black text-slate-900">{data.anomaly_rate}%</div>
              <div className="text-[9px] text-slate-400 mt-1">Percentage of total rows flagged</div>
            </div>

            <div className="kpi-card flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider">Top Vulnerable KPI</span>
                <BarChart2 size={14} className="text-blue-500" />
              </div>
              <div className="text-base font-black text-slate-900 truncate">
                {Object.keys(data.column_anomaly_counts || {}).length > 0 
                  ? Object.keys(data.column_anomaly_counts).sort((a,b) => data.column_anomaly_counts[b] - data.column_anomaly_counts[a])[0]
                  : 'None'
                }
              </div>
              <div className="text-[9px] text-slate-400 mt-1">Column with highest outlier count</div>
            </div>
          </div>

          {/* Main Layout split */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-2">
            {/* Left Column: Anomalies list */}
            <div className="lg:col-span-2 space-y-4">
              <h2 className="font-extrabold text-base text-slate-800 mb-2 flex items-center gap-1.5">
                <Layers size={18} className="text-blue-600" />
                Critical & High Impact Outliers
              </h2>
              {data.anomalies.length === 0 ? (
                <div className="card text-center py-16">
                  <ShieldAlert size={32} className="text-emerald-500 mx-auto mb-2" />
                  <p className="font-semibold text-slate-700">No anomalies found</p>
                  <p className="text-xs text-slate-400">All data patterns are behaving within normal parameters.</p>
                </div>
              ) : (
                data.anomalies.map((a: Anomaly, i: number) => (
                  <AnomalyCard key={i} anomaly={a} />
                ))
              )}
            </div>

            {/* Right Column: Sidebar summaries */}
            <div className="space-y-6">
              {/* Severity Breakdown */}
              <div className="card card-body">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">
                  Severity Distribution
                </h3>
                <div className="space-y-3">
                  <SeverityRow label="Critical" count={data.severity_breakdown.critical || 0} color="#EF4444" total={data.total_anomalies} />
                  <SeverityRow label="High" count={data.severity_breakdown.high || 0} color="#F59E0B" total={data.total_anomalies} />
                  <SeverityRow label="Medium" count={data.severity_breakdown.medium || 0} color="#3B82F6" total={data.total_anomalies} />
                  <SeverityRow label="Low" count={data.severity_breakdown.low || 0} color="#10B981" total={data.total_anomalies} />
                </div>
              </div>

              {/* Column Impact counts */}
              {Object.keys(data.column_anomaly_counts || {}).length > 0 && (
                <div className="card card-body">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">
                    Vulnerable Column Impact
                  </h3>
                  <div className="space-y-3">
                    {Object.entries(data.column_anomaly_counts)
                      .sort((a, b) => b[1] - a[1])
                      .slice(0, 5)
                      .map(([col, count], idx) => {
                        const pct = data.total_anomalies > 0 ? (count / data.total_anomalies) * 100 : 0
                        return (
                          <div key={idx} className="space-y-1">
                            <div className="flex justify-between text-xs font-semibold">
                              <span className="text-slate-700 truncate max-w-[150px]">{col}</span>
                              <span className="text-slate-400">{count} anomalies</span>
                            </div>
                            <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                              <div className="h-full bg-blue-600 rounded-full" style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        )
                      })}
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      ) : null}
    </div>
  )
}

function AnomalyCard({ anomaly }: { anomaly: Anomaly }) {
  const isCritical = anomaly.severity === 'critical' || anomaly.severity === 'high'
  const Icon = isCritical ? AlertCircle : Info
  
  const colors: Record<string, string> = {
    critical: '#EF4444',
    high: '#F59E0B',
    medium: '#3B82F6',
    low: '#10B981'
  }
  const bgColors: Record<string, string> = {
    critical: '#FEF2F2',
    high: '#FFFBEB',
    medium: '#EFF6FF',
    low: '#ECFDF5'
  }

  const border = colors[anomaly.severity] || '#64748B'
  const bg = bgColors[anomaly.severity] || '#F8FAFC'

  return (
    <div className="card border-l-4 bg-white shadow-sm hover:shadow-md transition-shadow" style={{ borderLeftColor: border }}>
      <div className="p-5">
        <div className="flex items-start gap-4">
          <div className="p-2 rounded-xl mt-1 flex-shrink-0" style={{ background: bg, color: border }}>
            <Icon size={20} />
          </div>
          <div className="flex-1 min-w-0 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Affected KPI: {anomaly.affected_kpi || 'Unknown'}</span>
                <h4 className="font-extrabold text-sm text-slate-900 mt-0.5">Record Index #{anomaly.index}</h4>
              </div>
              <span className="text-[10px] font-black px-2 py-1 rounded-full uppercase tracking-wider"
                    style={{ background: bg, color: border }}>
                {anomaly.severity}
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed font-medium bg-slate-50/55 p-3 rounded-lg border border-slate-100">
              {anomaly.explanation}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl space-y-1">
                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Likely Cause</span>
                <p className="text-xs font-medium text-slate-700 leading-normal">{anomaly.likely_cause || 'Out-of-bounds metrics'}</p>
              </div>
              
              <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl space-y-1">
                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Expected Normal Range</span>
                <p className="text-xs font-bold text-slate-700 leading-normal">{anomaly.expected_range || 'N/A'}</p>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl space-y-1">
                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Consensus Methods</span>
                <p className="text-[10px] font-semibold text-slate-500 leading-normal italic">{anomaly.method || 'Standard check'}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
              <div className="p-3 bg-red-50/25 border border-red-100/35 rounded-xl space-y-1">
                <span className="text-[9px] font-bold text-red-500 uppercase tracking-wider">Business Impact</span>
                <p className="text-xs font-medium text-slate-700 leading-relaxed">{anomaly.business_impact}</p>
              </div>
              <div className="p-3 bg-emerald-50/25 border border-emerald-100/35 rounded-xl space-y-1">
                <span className="text-[9px] font-bold text-emerald-600 uppercase tracking-wider">Recommended Action</span>
                <p className="text-xs font-medium text-slate-700 leading-relaxed">{anomaly.recommendation}</p>
              </div>
            </div>

            {Object.keys(anomaly.values || {}).length > 0 && (
              <div className="flex flex-wrap gap-2 pt-1 border-t border-slate-50 mt-2">
                {Object.entries(anomaly.values).map(([k, v]: [string, SafeAny], idx) => (
                  <span key={idx} className="text-[10px] px-2 py-0.5 rounded border border-slate-100 bg-slate-50/50"
                        style={{ color: 'var(--color-text-secondary)' }}>
                    <strong className="text-slate-400">{k}:</strong> {String(v || '')}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function SeverityRow({ label, count, color, total }: { label: string, count: number, color: string, total: number }) {
  const pct = total > 0 ? (count / total) * 100 : 0
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 font-semibold">
          <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
          <span className="text-slate-700">{label}</span>
        </div>
        <span className="font-extrabold text-slate-900">{count} <span className="text-[10px] text-slate-400 font-normal">({pct.toFixed(0)}%)</span></span>
      </div>
      <div className="w-full h-1 bg-slate-100 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ background: color, width: `${pct}%` }} />
      </div>
    </div>
  )
}

function NoDataset({ label }: { label: string }) {
  return (
    <div className="text-center py-20 animate-fade-in card bg-white border border-slate-200 rounded-2xl shadow-sm">
      <AlertTriangle size={48} className="text-slate-300 mx-auto mb-3" />
      <h2 className="font-extrabold text-lg text-slate-900 mb-1">{label}</h2>
      <p className="text-xs text-slate-400">Please upload a valid dataset in the workspace first to execute outlier audits.</p>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="text-center py-20 animate-pulse space-y-4">
      <div className="w-12 h-12 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mx-auto">
        <Activity size={24} />
      </div>
      <div>
        <h2 className="font-extrabold text-base text-slate-800">Compiling Model Consensus</h2>
        <p className="text-xs text-slate-400">Evaluating dataset using Isolation Forest, IQR, MAD, and seasonal filters...</p>
      </div>
    </div>
  )
}
