import { Check, ShieldCheck } from 'lucide-react'
import { useAuth } from '../lib/auth'

export default function PricingPage() {
  const { user } = useAuth()
  const isGuest = user?.role === 'guest'

  const plans = [
    {
      name: 'Guest Playbook',
      price: '$0',
      period: 'Forever',
      desc: 'Test the waters and explore standard insights on uploaded datasets.',
      features: [
        'Upload datasets (CSV, JSON, Excel)',
        'Automatic dashboard layouts',
        'KPI metrics calculation',
        'Interactive forecast chart generation',
        'Raw CSV and Excel data downloads',
        'Basic outlier and anomaly logs',
      ],
      cta: isGuest ? 'Active Tier' : 'Access as Guest',
      active: isGuest,
      popular: false,
    },
    {
      name: 'Professional Team',
      price: '$49',
      period: 'month',
      desc: 'Unlock complete boardroom ready export reporting and cloud storage.',
      features: [
        'Save unlimited active datasets',
        'Export Executive Summaries (PDF)',
        'Export slide presentations (PPTX)',
        'Generate shareable dashboard links',
        '50GB secure cloud storage',
        'Custom workspace name customization',
        'Email report digests',
      ],
      cta: 'Upgrade to Professional',
      active: false,
      popular: true,
    },
    {
      name: 'Enterprise Command',
      price: 'Custom',
      period: 'tailored',
      desc: 'Deep integration, custom schemas, and high performance computing.',
      features: [
        'Everything in Professional',
        'Multi-user shared workspaces',
        'Live dataset integration APIs',
        'Dedicated server processing limits',
        'Custom branding & styling layouts',
        '24/7 SLA operations support',
      ],
      cta: 'Contact Operations',
      active: false,
      popular: false,
    },
  ]

  return (
    <div className="animate-fade-in max-w-5xl mx-auto py-12 space-y-12">
      <div className="text-center space-y-4">
        <span className="text-xs font-semibold px-3.5 py-1.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 uppercase tracking-wider">
          SaaS Pricing Plans
        </span>
        <h1 className="text-4xl font-extrabold text-slate-900 dark:text-white sm:text-5xl">
          Simple, Transparent <span className="text-blue-600">Subscriptions</span>
        </h1>
        <p className="max-w-2xl mx-auto text-lg text-slate-500 dark:text-slate-400">
          Upload datasets without creating an account. Upgrade when you need executive-level deliverables, cloud persistence, or integrations.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 pt-6">
        {plans.map((p, i) => (
          <div
            key={i}
            className={`relative flex flex-col justify-between p-8 bg-white dark:bg-slate-900 border rounded-2xl shadow-sm transition-all duration-300 ${
              p.popular
                ? 'border-blue-500 ring-2 ring-blue-500/25 scale-105 z-10'
                : 'border-slate-200 dark:border-slate-800'
            }`}
          >
            {p.popular && (
              <span className="absolute top-0 right-6 -translate-y-1/2 px-3 py-1 bg-blue-600 text-white text-[10px] font-bold uppercase tracking-wider rounded-full shadow-sm">
                Most Popular
              </span>
            )}
            
            <div>
              <div className="mb-4">
                <h3 className="text-lg font-bold text-slate-800 dark:text-white">{p.name}</h3>
                <p className="text-xs text-slate-500 mt-1">{p.desc}</p>
              </div>

              <div className="flex items-baseline gap-1.5 my-6">
                <span className="text-4xl font-extrabold text-slate-900 dark:text-white">{p.price}</span>
                <span className="text-sm text-slate-500">/{p.period}</span>
              </div>

              <ul className="space-y-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                {p.features.map((f, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-sm text-slate-600 dark:text-slate-350">
                    <Check className="text-blue-600 flex-shrink-0 mt-0.5" size={16} />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>

            <button
              className={`btn w-full mt-8 flex justify-center py-2.5 rounded-xl font-bold text-sm ${
                p.active
                  ? 'bg-slate-100 dark:bg-slate-800 text-slate-500 cursor-default border border-slate-200 dark:border-slate-700'
                  : p.popular
                  ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/10'
                  : 'bg-slate-800 hover:bg-slate-700 text-white'
              }`}
            >
              {p.cta}
            </button>
          </div>
        ))}
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-4 bg-slate-50 dark:bg-slate-950/20 border border-slate-100 dark:border-slate-850 p-6 rounded-2xl max-w-3xl mx-auto mt-12 text-center sm:text-left">
        <ShieldCheck className="text-blue-600 flex-shrink-0" size={32} />
        <div>
          <h4 className="font-bold text-slate-800 dark:text-white text-sm">Security & Isolation Guarantee</h4>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            All dataset operations run in isolated sandbox environments. In Guest mode, data uploads are stored temporarily in your local browser storage and session logs, completely cleared on page close.
          </p>
        </div>
      </div>
    </div>
  )
}
