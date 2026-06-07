import { useQuery } from '@tanstack/react-query'
import { getKPIs, getTrends, getTopPerformers } from '../lib/api'
import { BarChart3, ArrowUpRight, ArrowDownRight, Minus, TrendingUp } from 'lucide-react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import type { SafeAny } from '../types'

const CHART_COLORS = ['#2563EB', '#7C3AED', '#059669', '#D97706', '#DC2626', '#0891B2', '#4F46E5', '#EA580C']

interface Props {
  datasetId: string | null
}

export default function KPIDashboard({ datasetId }: Props) {
  const { data: kpiData, isLoading: kpiLoading } = useQuery({
    queryKey: ['kpis', datasetId],
    queryFn: () => getKPIs(datasetId!),
    enabled: !!datasetId,
  })

  const { data: trendData } = useQuery({
    queryKey: ['trends', datasetId],
    queryFn: () => getTrends(datasetId!),
    enabled: !!datasetId,
  })

  const { data: topData } = useQuery({
    queryKey: ['top-performers', datasetId],
    queryFn: () => getTopPerformers(datasetId!),
    enabled: !!datasetId,
  })

  if (!datasetId) return <NoDataset label="KPI Dashboard" />

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">KPI Dashboard</h1>
        <p className="page-subtitle">
          {kpiData?.domain ? `${kpiData.domain} domain metrics` : 'Auto-detected business metrics'}
        </p>
      </div>

      {/* KPI Cards */}
      {(kpiData?.kpis?.length || 0) > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {kpiData?.kpis?.map((kpi: SafeAny, i: number) => {
            const TrendIcon = kpi.trend === 'up' ? ArrowUpRight : kpi.trend === 'down' ? ArrowDownRight : Minus
            const trendColor = kpi.trend === 'up' ? 'var(--color-success)' : kpi.trend === 'down' ? 'var(--color-danger)' : 'var(--color-text-muted)'
            return (
              <div key={i} className="kpi-card">
                <div className="text-sm font-medium mb-1" style={{ color: 'var(--color-text-secondary)' }}>
                  {kpi.icon} {kpi.name}
                </div>
                <div className="font-extrabold text-2xl mb-1" style={{ color: 'var(--color-text-primary)' }}>
                  {kpi.formatted_value}
                </div>
                <div className="flex items-center gap-1 text-xs font-semibold" style={{ color: trendColor }}>
                  <TrendIcon size={14} />
                  {kpi.trend_value !== 0 ? `${kpi.trend_value > 0 ? '+' : ''}${kpi.trend_value}%` : 'Stable'}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-8">
        {/* Trend Chart */}
        {(trendData?.trends?.[0]?.data_points?.length || 0) > 0 && (
          <div className="card card-body">
            <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--color-text-primary)' }}>
              <TrendingUp size={16} className="inline mr-2" />
              {trendData?.trends?.[0]?.column} Trend
            </h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={trendData?.trends?.[0]?.data_points}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #E2E8F0', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }} />
                <Line type="monotone" dataKey="value" stroke="#2563EB" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Top Performers Bar Chart */}
        {(topData?.items?.length || 0) > 0 && (
          <div className="card card-body">
            <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--color-text-primary)' }}>
              <BarChart3 size={16} className="inline mr-2" />
              Top {topData?.dimension} by {topData?.metric}
            </h3>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={topData?.items?.slice(0, 8)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 11, fill: '#64748B' }} />
                <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #E2E8F0' }} />
                <Bar dataKey="sum" radius={[0, 6, 6, 0]}>
                  {topData?.items?.slice(0, 8).map((_: SafeAny, i: number) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {kpiLoading && <LoadingBar />}
    </div>
  )
}

function NoDataset({ label }: { label: string }) {
  return (
    <div className="text-center py-20 animate-fade-in">
      <BarChart3 size={48} style={{ color: 'var(--color-text-muted)', margin: '0 auto 1rem' }} />
      <h2 className="font-bold text-xl mb-2" style={{ color: 'var(--color-text-primary)' }}>{label}</h2>
      <p style={{ color: 'var(--color-text-secondary)' }}>Upload a dataset to see analytics</p>
    </div>
  )
}

function LoadingBar() {
  return (
    <div className="w-full h-1 rounded-full overflow-hidden" style={{ background: 'var(--color-border-light)' }}>
      <div className="h-full rounded-full animate-pulse" style={{ width: '60%', background: 'var(--color-primary)' }} />
    </div>
  )
}
