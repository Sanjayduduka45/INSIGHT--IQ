import { Shield, Sparkles, Cpu } from 'lucide-react'

export default function AboutPage() {
  return (
    <div className="animate-fade-in max-w-4xl mx-auto py-12 space-y-12">
      <div className="text-center space-y-4">
        <span className="text-xs font-semibold px-3.5 py-1.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 uppercase tracking-wider">
          Our Architecture
        </span>
        <h1 className="text-4xl font-extrabold text-slate-900 dark:text-white sm:text-5xl">
          About <span className="text-blue-600">InsightIQ</span>
        </h1>
        <p className="max-w-2xl mx-auto text-lg text-slate-500 dark:text-slate-400">
          Bridging the gap between raw datasets and executive decisions with state-of-the-art AI reasoning models.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-6">
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
            <Cpu className="text-blue-600" size={20} />
            The Intelligence Engine
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
            InsightIQ operates on a dual-engine architecture:
          </p>
          <ul className="space-y-3 pl-2 text-sm text-slate-600 dark:text-slate-350">
            <li className="flex items-start gap-2.5">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-2 flex-shrink-0" />
              <span>
                <strong>Analytical Ingest</strong>: An advanced statistical miner that detects variable boundaries, quality anomalies, correlation grids, and optimal time series dimensions automatically.
              </span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-2 flex-shrink-0" />
              <span>
                <strong>LLM Reasoner</strong>: Integrated directly with advanced reasoning models, allowing users to query data in natural language, ask for recommendations, and compile slide decks in real time.
              </span>
            </li>
          </ul>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
            <Shield className="text-blue-600" size={20} />
            Secure & Sandboxed
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
            Data security is our primary focus. We implement complete sandbox isolation:
          </p>
          <ul className="space-y-3 pl-2 text-sm text-slate-600 dark:text-slate-350">
            <li className="flex items-start gap-2.5">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-2 flex-shrink-0" />
              <span>
                <strong>Zero Leakage</strong>: Raw files are kept in highly secured temporary folders or client-side storage boundaries depending on registration levels.
              </span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-2 flex-shrink-0" />
              <span>
                <strong>Encrypted Communications</strong>: Every analytical scoring, chart generation, or forecast payload is sent via encrypted channels to secure computing systems.
              </span>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-slate-200 dark:border-slate-800 pt-10 text-center space-y-4">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center justify-center gap-2">
          <Sparkles className="text-purple-600 animate-pulse" size={20} />
          Transforming Data Into Decisions
        </h3>
        <p className="max-w-xl mx-auto text-sm text-slate-500 dark:text-slate-400">
          Our mission is to democratize advanced data analytics. You shouldn't need a degree in data science or software engineering to understand your customer churn, predict revenue growth, or spot outlier expenses. InsightIQ is built for everyone.
        </p>
      </div>
    </div>
  )
}
