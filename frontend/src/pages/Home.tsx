import { useQuery } from '@tanstack/react-query'
import { getOverview } from '../lib/api'
import {
  Upload, BarChart3, AlertTriangle, TrendingUp,
  MessageSquare, Database, ArrowUpRight, ArrowDownRight,
  Minus, Sparkles, Zap, Shield
} from 'lucide-react'
import type { SafeAny } from '../types'

interface HomeProps {
  datasetId: string | null
  onNavigate: (path: string) => void
}

export default function HomePage({ datasetId, onNavigate }: HomeProps) {
  if (!datasetId) {
    return <WelcomeView onNavigate={onNavigate} />
  }
  return <DashboardView datasetId={datasetId} />
}

// ── Welcome (No Dataset) ────────────────────────────────────────────────

function WelcomeView({ onNavigate }: { onNavigate: (p: string) => void }) {
  const features = [
    { icon: Upload, title: 'Upload Data', desc: 'CSV, Excel, Parquet, JSON with auto-detection', path: '/upload', color: '#2563EB' },
    { icon: MessageSquare, title: 'AI Chat', desc: 'Natural language analytics with AI reasoning', path: '/chat', color: '#7C3AED' },
    { icon: BarChart3, title: 'KPI Dashboard', desc: 'Auto-detected business metrics & trends', path: '/kpi', color: '#059669' },
    { icon: AlertTriangle, title: 'Anomaly Center', desc: 'Outlier detection & root cause analysis', path: '/anomalies', color: '#DC2626' },
    { icon: TrendingUp, title: 'Forecasting', desc: 'Multi-model predictions with confidence intervals', path: '/forecast', color: '#D97706' },
    { icon: Database, title: 'Data Quality', desc: 'Quality scoring across 5 dimensions', path: '/quality', color: '#0891B2' },
  ]

  return (
    <div className="animate-fade-in">
      {/* Hero Section */}
      <div className="text-center mb-12" style={{ paddingTop: '3rem' }}>
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full mb-6"
             style={{ background: 'var(--color-primary-50)', color: 'var(--color-primary)' }}>
          <Sparkles size={14} />
          <span className="text-xs font-semibold uppercase tracking-wider">AI-Powered Analytics</span>
        </div>
        <h1 className="font-extrabold tracking-tight mb-4"
             style={{ fontSize: '2.75rem', color: 'var(--color-text-primary)', lineHeight: 1.1 }}>
          Upload Any Dataset.
          <br />
          <span style={{ color: 'var(--color-primary)' }}>Get Expert-Level Insights.</span>
        </h1>
        <p className="text-lg max-w-xl mx-auto" style={{ color: 'var(--color-text-secondary)' }}>
          InsightIQ automatically understands your data, detects patterns, identifies anomalies,
          and delivers actionable intelligence — no coding required.
        </p>
        <button
          onClick={() => onNavigate('/upload')}
          className="btn btn-primary mt-8"
          style={{ padding: '0.875rem 2.5rem', fontSize: '1rem', borderRadius: 'var(--radius-lg)' }}
        >
          <Upload size={20} />
          Upload Your Dataset
        </button>
      </div>

      {/* Feature Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 max-w-5xl mx-auto">
        {features.map((f) => (
          <button
            key={f.path}
            onClick={() => onNavigate(f.path)}
            className="feature-card text-left"
            style={{ background: `linear-gradient(135deg, ${f.color}, ${f.color}dd)` }}
          >
            <f.icon size={28} className="mb-3 opacity-90" />
            <div className="font-bold text-lg mb-1">{f.title}</div>
            <div className="text-sm opacity-80">{f.desc}</div>
          </button>
        ))}
      </div>

      {/* Capabilities strip */}
      <div className="flex flex-wrap justify-center gap-6 mt-12 pb-8">
        {['Sales', 'Finance', 'Healthcare', 'HR', 'Manufacturing', 'Logistics', 'Education', 'IoT'].map((d) => (
          <span key={d} className="text-xs font-medium px-3 py-1 rounded-full"
                style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)' }}>
            {d}
          </span>
        ))}
      </div>
    </div>
  )
}

// ── Dashboard (Dataset Loaded) ──────────────────────────────────────────

function DashboardView({ datasetId }: { datasetId: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['overview', datasetId],
    queryFn: () => getOverview(datasetId),
    enabled: !!datasetId,
  })

  if (isLoading) return <LoadingSkeleton />
  if (error) return <ErrorState message={(error as Error).message} />
  if (!data) return null

  return (
    <div className="animate-fade-in">
      {/* Page Header */}
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">{data.dataset_name}</h1>
          <p className="page-subtitle">
            {data.domain?.name} · {Number(data.quick_stats?.rows || 0).toLocaleString()} rows · {data.quick_stats?.columns} columns
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="badge badge-info">{data.domain?.name}</div>
          <div className={`badge ${data.health_scores?.data_quality_grade === 'A' ? 'badge-success' : data.health_scores?.data_quality_grade === 'B' ? 'badge-info' : 'badge-warning'}`}>
            Grade {data.health_scores?.data_quality_grade}
          </div>
        </div>
      </div>

      {/* Health Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        <HealthCard
          title="Business Health"
          score={Number(data.health_scores?.business || 0)}
          icon={<Zap size={20} />}
          color="#2563EB"
        />
        <HealthCard
          title="Data Quality"
          score={Number(data.health_scores?.data_quality || 0)}
          icon={<Shield size={20} />}
          color="#059669"
        />
        <HealthCard
          title="Quality Grade"
          score={null}
          label={String(data.health_scores?.data_quality_grade || '')}
          icon={<Sparkles size={20} />}
          color="#7C3AED"
        />
      </div>

      {/* KPI Cards */}
      {(data.kpis?.length || 0) > 0 && (
        <div className="mb-8">
          <h2 className="font-bold text-lg mb-4" style={{ color: 'var(--color-text-primary)' }}>
            Key Performance Indicators
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {data.kpis?.map((kpi: SafeAny, i: number) => (
              <KPICard key={i} kpi={kpi} />
            ))}
          </div>
        </div>
      )}

      {/* Insights */}
      {(data.insights?.length || 0) > 0 && (
        <div>
          <h2 className="font-bold text-lg mb-4" style={{ color: 'var(--color-text-primary)' }}>
            AI-Generated Insights
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.insights?.map((insight: SafeAny, i: number) => (
              <InsightCard key={i} insight={insight} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Sub-components ──────────────────────────────────────────────────────

function HealthCard({ title, score, label, icon, color }: {
  title: string; score: number | null; label?: string; icon: React.ReactNode; color: string
}) {
  return (
    <div className="kpi-card">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white" style={{ background: color }}>
          {icon}
        </div>
        <div className="text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>{title}</div>
      </div>
      <div className="font-extrabold text-3xl" style={{ color: 'var(--color-text-primary)' }}>
        {label || `${score?.toFixed(0)}%`}
      </div>
    </div>
  )
}

function KPICard({ kpi }: { kpi: SafeAny }) {
  const TrendIcon = kpi.trend === 'up' ? ArrowUpRight : kpi.trend === 'down' ? ArrowDownRight : Minus
  const trendColor = kpi.trend === 'up' ? 'var(--color-success)' : kpi.trend === 'down' ? 'var(--color-danger)' : 'var(--color-text-muted)'

  return (
    <div className="kpi-card">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>
          {kpi.icon} {kpi.name}
        </span>
        <div className="flex items-center gap-1 text-xs font-semibold" style={{ color: trendColor }}>
          <TrendIcon size={14} />
          {kpi.trend_value !== 0 && `${kpi.trend_value > 0 ? '+' : ''}${kpi.trend_value}%`}
        </div>
      </div>
      <div className="font-extrabold text-2xl" style={{ color: 'var(--color-text-primary)' }}>
        {kpi.formatted_value}
      </div>
    </div>
  )
}

function InsightCard({ insight }: { insight: SafeAny }) {
  const colors: Record<string, string> = {
    positive: 'var(--color-success)',
    warning: 'var(--color-warning)',
    info: 'var(--color-info)',
  }

  const hasFourParts = !!(insight.observation || insight.evidence || insight.business_impact || insight.recommendation)

  return (
    <div className="card card-body hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className="w-2.5 h-2.5 rounded-full mt-2 flex-shrink-0"
             style={{ background: colors[insight.severity] || 'var(--color-info)' }} />
        <div className="flex-1 min-w-0">
          {hasFourParts ? (
            <div className="space-y-3">
              <div className="font-bold text-sm" style={{ color: 'var(--color-text-primary)', fontSize: '0.95rem' }}>
                {insight.observation || insight.title}
              </div>
              <div className="grid gap-2 text-xs border-t pt-3" style={{ borderColor: 'var(--color-border-light)' }}>
                {insight.evidence && (
                  <div>
                    <span className="font-bold text-slate-500 uppercase tracking-wider block mb-0.5" style={{ fontSize: '0.65rem' }}>Data Evidence</span>
                    <span style={{ color: 'var(--color-text-secondary)' }}>{insight.evidence}</span>
                  </div>
                )}
                {insight.business_impact && (
                  <div>
                    <span className="font-bold text-slate-500 uppercase tracking-wider block mb-0.5" style={{ fontSize: '0.65rem' }}>Business Impact</span>
                    <span style={{ color: 'var(--color-text-secondary)' }}>{insight.business_impact}</span>
                  </div>
                )}
                {insight.recommendation && (
                  <div className="mt-1 p-2 rounded-lg bg-emerald-50/50 border border-emerald-100/30">
                    <span className="font-bold text-emerald-600 uppercase tracking-wider block mb-0.5" style={{ fontSize: '0.65rem' }}>Action Recommendation</span>
                    <span className="font-medium text-emerald-800">{insight.recommendation}</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div>
              <div className="font-semibold text-sm mb-1" style={{ color: 'var(--color-text-primary)' }}>
                {insight.title}
              </div>
              <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                {insight.description}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="animate-fade-in">
      <div className="h-8 w-64 rounded-lg mb-2" style={{ background: 'var(--color-border-light)' }} />
      <div className="h-4 w-96 rounded mb-8" style={{ background: 'var(--color-border-light)' }} />
      <div className="grid grid-cols-3 gap-5 mb-8">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-32 rounded-xl" style={{ background: 'var(--color-border-light)' }} />
        ))}
      </div>
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="h-24 rounded-xl" style={{ background: 'var(--color-border-light)' }} />
        ))}
      </div>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="text-center py-20">
      <AlertTriangle size={48} style={{ color: 'var(--color-warning)', margin: '0 auto 1rem' }} />
      <h2 className="font-bold text-xl mb-2">Something went wrong</h2>
      <p style={{ color: 'var(--color-text-secondary)' }}>{message}</p>
    </div>
  )
}
