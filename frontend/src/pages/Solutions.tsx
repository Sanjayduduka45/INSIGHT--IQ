import { TrendingUp, Users, Shield, Building2 } from 'lucide-react'

export default function SolutionsPage() {
  const solutions = [
    {
      icon: TrendingUp,
      title: 'Finance & Revenue Operations',
      desc: 'Analyze sales metrics, calculate recurring revenues (MRR/ARR), map customer lifetime value, and run growth forecast scenarios with precision.',
      benefits: ['Dynamic revenue growth rates', 'Predictive cash flow modeling', 'Category performance breakdowns'],
      colorHex: '#2563EB'
    },
    {
      icon: Users,
      title: 'Customer Intelligence & Marketing',
      desc: 'Understand retention behaviors, track cohort churn rates, map repeat purchase metrics, and optimize customer spend allocations.',
      benefits: ['Churn vulnerability scores', 'Customer spend distribution charts', 'Repeat account ratios'],
      colorHex: '#7C3AED'
    },
    {
      icon: Building2,
      title: 'Business & Team Operations',
      desc: 'Identify structural bottlenecks, outlier expenses, volume productivity issues, and automate regular executive summary reports.',
      benefits: ['Diagnostic anomaly logging', 'Executive reporting deck compilers', 'Consensus outlier scoring'],
      colorHex: '#059669'
    },
    {
      icon: Shield,
      title: 'Enterprise Risk & Quality Audits',
      desc: 'Scan large operational datasets to verify column distributions, data completeness, value ranges, and statistical consistency.',
      benefits: ['Completeness and validity metrics', 'Outlier risk isolation', 'Correlation redundancy detection'],
      colorHex: '#DC2626'
    }
  ]

  return (
    <div className="animate-fade-in max-w-5xl mx-auto py-12 space-y-12">
      <div className="text-center space-y-4">
        <span className="text-xs font-semibold px-3.5 py-1.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 uppercase tracking-wider">
          Enterprise Workflows
        </span>
        <h1 className="text-4xl font-extrabold text-slate-900 dark:text-white sm:text-5xl">
          Solutions for <span className="text-blue-600">Every Department</span>
        </h1>
        <p className="max-w-2xl mx-auto text-lg text-slate-500 dark:text-slate-400">
          InsightIQ handles diverse dataset domains out-of-the-box. We ingest, label, analyze, and generate metrics custom-tailored to your industry.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-6">
        {solutions.map((s, i) => (
          <div
            key={i}
            className="feature-card text-left flex flex-col justify-between"
            style={{ 
              background: `linear-gradient(135deg, ${s.colorHex}, ${s.colorHex}dd)`,
              cursor: 'default'
            }}
          >
            <div>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-white/10 border border-white/20 mb-6 text-white">
                <s.icon size={22} />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">{s.title}</h3>
              <p className="text-sm opacity-85 leading-relaxed mb-6">{s.desc}</p>
              
              <div className="border-t border-white/15 pt-6">
                <h4 className="text-xs font-bold uppercase tracking-wider opacity-75 mb-3">
                  Key Capabilities
                </h4>
                <ul className="space-y-2">
                  {s.benefits.map((b, idx) => (
                    <li key={idx} className="flex items-center gap-2.5 text-sm opacity-90">
                      <span className="w-1.5 h-1.5 rounded-full bg-white flex-shrink-0" />
                      {b}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
