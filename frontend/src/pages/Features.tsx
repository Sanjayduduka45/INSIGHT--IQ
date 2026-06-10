import { Sparkles, BarChart3, AlertTriangle, TrendingUp, MessageSquare, Database, GitBranch } from 'lucide-react'

export default function FeaturesPage() {
  const features = [
    {
      icon: MessageSquare,
      title: 'AI Conversational Analytics',
      desc: 'Ask questions about your data in plain English. The AI reasons over data schemas, runs statistical checks, and provides rich graphical insights.',
      color: '#7C3AED',
    },
    {
      icon: BarChart3,
      title: 'Automated KPI Dashboards',
      desc: 'No manual configuration required. InsightIQ scans your dataset on upload, detects primary metrics (revenue, churn, scores), and plots beautiful key trends.',
      color: '#059669',
    },
    {
      icon: TrendingUp,
      title: 'Predictive Forecasting Engine',
      desc: 'Model future growth vectors using advanced statistical models. Get multi-period projections, lower/upper bounds, and confidence interval charts.',
      color: '#D97706',
    },
    {
      icon: AlertTriangle,
      title: 'Consensus Outlier Analysis',
      desc: 'Detect data anomalies using isolation forests, z-scores, and IQR consensus models. Instantly pinpoint root causes and business variance sources.',
      color: '#DC2626',
    },
    {
      icon: Database,
      title: 'Deep Data Quality Scoring',
      desc: 'Evaluate dataset health across completeness, consistency, range validity, and correlation density, returning a letter-grade score card.',
      color: '#0891B2',
    },
    {
      icon: GitBranch,
      title: 'Multi-Variable Correlation Miner',
      desc: 'Explore linear and non-linear relationships. Identify how drivers interact and filter out redundant variables automatically.',
      color: '#2563EB',
    },
  ]

  return (
    <div className="animate-fade-in max-w-5xl mx-auto py-12 space-y-12">
      <div className="text-center space-y-4">
        <div className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 text-xs font-semibold tracking-wider uppercase">
          <Sparkles size={14} />
          Intelligence Platform
        </div>
        <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white sm:text-5xl">
          Engineered for <span className="text-blue-600">Decision Makers</span>
        </h1>
        <p className="max-w-2xl mx-auto text-lg text-slate-500 dark:text-slate-400">
          InsightIQ automates the entire analytics pipeline. From raw CSV ingestion to executive boardroom presentations, we do it in seconds.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pt-6">
        {features.map((f, i) => (
          <div
            key={i}
            className="feature-card text-left"
            style={{ 
              background: `linear-gradient(135deg, ${f.color}, ${f.color}dd)`,
              cursor: 'default'
            }}
          >
            <f.icon size={28} className="mb-3 opacity-90" />
            <h3 className="font-bold text-lg mb-1 text-white">
              {f.title}
            </h3>
            <p className="text-sm opacity-85 leading-relaxed">
              {f.desc}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
