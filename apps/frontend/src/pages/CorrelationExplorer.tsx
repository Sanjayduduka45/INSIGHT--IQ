/**
 * InsightIQ — Correlation Explorer
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getCorrelations, getDistributions } from '../lib/api'
import { GitBranch, Activity } from 'lucide-react'
import type { SafeAny } from '../types'


interface Props {
  datasetId: string | null
}

export default function CorrelationExplorer({ datasetId }: Props) {
  const [method, setMethod] = useState<'pearson' | 'spearman'>('pearson')

  const { data: corrData, isLoading: corrLoading } = useQuery({
    queryKey: ['correlations', datasetId, method],
    queryFn: () => getCorrelations(datasetId!, method),
    enabled: !!datasetId,
  })

  const { data: distData, isLoading: distLoading } = useQuery({
    queryKey: ['distributions', datasetId],
    queryFn: () => getDistributions(datasetId!),
    enabled: !!datasetId,
  })

  if (!datasetId) return <NoDataset />
  if (corrLoading || distLoading) return <LoadingState />
  if (!corrData || !distData) return null

  // Sort correlations by absolute magnitude safely
  const topCorrelations = [...(corrData?.top_correlations || [])]
    .sort((a, b) => Math.abs(b.correlation || b.value || 0) - Math.abs(a.correlation || a.value || 0))

  return (
    <div className="animate-fade-in">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">Correlation Explorer</h1>
          <p className="page-subtitle">Discover statistical relationships between metrics</p>
        </div>
        <div className="flex gap-2">
          <button 
            className={`px-3 py-1.5 rounded-md text-sm font-medium ${method === 'pearson' ? 'bg-blue-600 text-white' : 'bg-white text-slate-600 border border-slate-200'}`}
            onClick={() => setMethod('pearson')}
          >
            Pearson (Linear)
          </button>
          <button 
            className={`px-3 py-1.5 rounded-md text-sm font-medium ${method === 'spearman' ? 'bg-blue-600 text-white' : 'bg-white text-slate-600 border border-slate-200'}`}
            onClick={() => setMethod('spearman')}
          >
            Spearman (Rank)
          </button>
        </div>
      </div>

      {topCorrelations.length === 0 ? (
        <div className="card card-body text-center py-12">
          <p style={{ color: 'var(--color-text-secondary)' }}>Not enough numeric columns to compute correlations.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Correlations List */}
          <div className="card card-body">
            <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
              <GitBranch size={20} className="text-blue-600" />
              Strongest Relationships
            </h3>
            <div className="space-y-4">
              {topCorrelations.slice(0, 8).map((corr, i) => (
                <CorrelationRow key={i} corr={corr} />
              ))}
            </div>
          </div>

          {/* Feature Distributions */}
          <div className="card card-body">
            <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
              <Activity size={20} className="text-purple-600" />
              Metric Distributions
            </h3>
            <div className="space-y-6 max-h-[600px] overflow-y-auto pr-2">
              {(distData?.distributions || []).slice(0, 5).map((dist: SafeAny) => (
                <div key={dist.column} className="pb-4 border-b border-slate-100 last:border-0">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold text-slate-800">{dist.column}</span>
                    <span className="text-xs text-slate-500">Skewness: {(dist.skew || 0).toFixed(2)}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs mb-3">
                    <div className="bg-slate-50 p-2 rounded text-center">
                      <div className="text-slate-500 mb-1">Mean</div>
                      <div className="font-semibold">{(dist.mean || 0).toFixed(2)}</div>
                    </div>
                    <div className="bg-slate-50 p-2 rounded text-center">
                      <div className="text-slate-500 mb-1">Median</div>
                      <div className="font-semibold">{(dist.median || 0).toFixed(2)}</div>
                    </div>
                    <div className="bg-slate-50 p-2 rounded text-center">
                      <div className="text-slate-500 mb-1">Std Dev</div>
                      <div className="font-semibold">{(dist.std || 0).toFixed(2)}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function CorrelationRow({ corr }: { corr: SafeAny }) {
  const value = corr.correlation ?? corr.value ?? 0;
  const isPositive = value > 0
  const strength = Math.abs(value)
  
  let strengthLabel = 'Weak'
  if (strength >= 0.7) strengthLabel = 'Strong'
  else if (strength >= 0.4) strengthLabel = 'Moderate'

  const color = isPositive ? 'var(--color-success)' : 'var(--color-danger)'
  
  return (
    <div className="flex items-center justify-between p-3 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-800 mb-1">
          <span className="truncate max-w-[120px]" title={corr.col1}>{corr.col1}</span>
          <span className="text-slate-400">↔</span>
          <span className="truncate max-w-[120px]" title={corr.col2}>{corr.col2}</span>
        </div>
        <div className="text-xs text-slate-500">
          {strengthLabel} {isPositive ? 'positive' : 'negative'} correlation
        </div>
      </div>
      <div className="flex flex-col items-end">
        <div className="text-lg font-extrabold" style={{ color }}>
          {value > 0 ? '+' : ''}{value.toFixed(2)}
        </div>
        {/* Visual bar indicator */}
        <div className="w-16 h-1.5 bg-slate-200 rounded-full mt-1 overflow-hidden flex">
          {isPositive ? (
            <>
              <div className="w-1/2" />
              <div className="h-full bg-green-500" style={{ width: `${strength * 50}%` }} />
            </>
          ) : (
            <>
              <div className="h-full bg-red-500 ml-auto" style={{ width: `${strength * 50}%` }} />
              <div className="w-1/2" />
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function NoDataset() {
  return (
    <div className="text-center py-20 animate-fade-in">
      <GitBranch size={48} style={{ color: 'var(--color-text-muted)', margin: '0 auto 1rem' }} />
      <h2 className="font-bold text-xl mb-2" style={{ color: 'var(--color-text-primary)' }}>Correlation Explorer</h2>
      <p style={{ color: 'var(--color-text-secondary)' }}>Upload a dataset to find hidden relationships</p>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="text-center py-20 animate-pulse">
      <div className="inline-block p-4 rounded-full mb-4" style={{ background: 'var(--color-primary-50)' }}>
        <GitBranch size={32} style={{ color: 'var(--color-primary)' }} />
      </div>
      <h2 className="font-bold text-lg mb-2">Analyzing Relationships</h2>
      <p style={{ color: 'var(--color-text-secondary)' }}>Computing correlation matrices and distributions...</p>
    </div>
  )
}
