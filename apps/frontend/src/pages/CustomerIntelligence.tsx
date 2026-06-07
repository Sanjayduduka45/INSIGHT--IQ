/**
 * InsightIQ — Customer Intelligence Dashboard
 */

import { useQuery } from '@tanstack/react-query'
import { getCustomerIntelligence } from '../lib/api'
import { 
  Users, Award, ShieldAlert, Sparkles, TrendingUp, BarChart3, 
  UsersRound, FileText, Heart, UserMinus, AlertTriangle
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import type { SafeAny } from '../types'

const CHART_COLORS = ['#10B981', '#3B82F6', '#6366F1', '#F59E0B', '#EF4444', '#64748B']

interface Props {
  datasetId: string | null
}

export default function CustomerIntelligence({ datasetId }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ['customer-intelligence', datasetId],
    queryFn: () => getCustomerIntelligence(datasetId!),
    enabled: !!datasetId,
  })

  if (!datasetId) return <NoDataset />
  if (isLoading) return <LoadingState />
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

  // Prep Segment Chart Data
  const segmentChart = Object.entries(data.segments || {}).map(([key, seg]: [string, any]) => ({
    name: seg.name,
    value: seg.total_spend,
    count: seg.customer_count,
    share: seg.share_percentage
  }))

  return (
    <div className="animate-fade-in space-y-8">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title flex items-center gap-2">
          <UsersRound className="text-indigo-600" />
          Customer Intelligence Hub
        </h1>
        <p className="page-subtitle">
          RFM segments (Champions, Loyal, At Risk, Lost), Customer Lifetime Value (CLV), and Pareto distribution
        </p>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="kpi-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[10px] font-bold uppercase tracking-wider">Total Active Customers</span>
            <Users size={16} className="text-blue-500" />
          </div>
          <div className="text-2xl font-black text-slate-900">{data.total_customers.toLocaleString()}</div>
          <div className="text-[9px] text-slate-400 mt-1 truncate">Unique customer entities binned</div>
        </div>

        <div className="kpi-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[10px] font-bold uppercase tracking-wider">Repeat Buyer Rate</span>
            <Heart size={16} className="text-rose-500" />
          </div>
          <div className="text-2xl font-black text-slate-900">{data.repeat_rate}%</div>
          <div className="text-[9px] text-slate-400 mt-1 truncate">
            {data.repeat_count} repeat accounts ({data.repeat_revenue_share}% of sales)
          </div>
        </div>

        <div className="kpi-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[10px] font-bold uppercase tracking-wider">Pareto 80/20 Index</span>
            <Award size={16} className="text-purple-500" />
          </div>
          <div className="text-2xl font-black text-slate-900">{data.pareto_80_20_customer_pct}%</div>
          <div className="text-[9px] text-slate-400 mt-1 truncate">
            Top {data.pareto_80_20_customer_pct}% of customers generate 80% of revenue
          </div>
        </div>

        <div className="kpi-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[10px] font-bold uppercase tracking-wider">Top 20% Spend Share</span>
            <TrendingUp size={16} className="text-emerald-500" />
          </div>
          <div className="text-2xl font-black text-slate-900">{data.pareto_20_concentration}%</div>
          <div className="text-[9px] text-slate-400 mt-1 truncate">Total revenue share of top 20%</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: RFM Segment Spend Share */}
        <div className="card card-body col-span-1 flex flex-col justify-between shadow-sm">
          <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-1.5">
              <BarChart3 size={16} className="text-indigo-600" />
              RFM Segment Revenue Share
            </h3>
            <div style={{ height: 200, width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={segmentChart}>
                  <XAxis dataKey="name" tick={{ fontSize: 9 }} hide />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                    {segmentChart.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="space-y-2.5 mt-4 border-t pt-4 border-slate-100">
            {Object.entries(data.segments || {}).map(([key, seg]: [string, any], idx: number) => (
              <div key={key} className="flex justify-between items-center text-xs">
                <span className="flex items-center gap-1.5 text-slate-500">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: CHART_COLORS[idx % CHART_COLORS.length] }} />
                  {seg.name} ({seg.customer_count})
                </span>
                <span className="font-semibold text-slate-900">
                  ${seg.total_spend.toLocaleString(undefined, { maximumFractionDigits: 0 })} ({seg.share_percentage}%)
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Customer Directory (Rankings, RFM, CLV, Churn Risk) */}
        <div className="lg:col-span-2 card card-body shadow-sm">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-1.5">
            <Award size={16} className="text-yellow-500" />
            Top Customer Segment Profiling Directory
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                  <th className="py-2.5">Rank</th>
                  <th className="py-2.5">Customer Identity</th>
                  <th className="py-2.5">RFM Segment</th>
                  <th className="py-2.5">Total Spend</th>
                  <th className="py-2.5">Orders</th>
                  <th className="py-2.5">Churn Risk</th>
                  <th className="py-2.5">Est. CLV</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.top_customers.map((c: any) => (
                  <tr key={c.rank} className="hover:bg-slate-50/50">
                    <td className="py-3 font-semibold text-slate-400">#{c.rank}</td>
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
                    <td className="py-3 font-semibold text-slate-800">${c.spend.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</td>
                    <td className="py-3 text-slate-600 font-medium">{c.transactions}</td>
                    <td className="py-3">
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full"
                              style={{ background: c.churn_risk > 70 ? '#EF4444' : c.churn_risk > 40 ? '#F59E0B' : '#10B981' }} />
                        <span className="font-semibold text-slate-700">{c.churn_risk}%</span>
                      </div>
                    </td>
                    <td className="py-3 font-bold text-slate-900">${c.clv.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
    </div>
  )
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
