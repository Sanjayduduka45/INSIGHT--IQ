/**
 * InsightIQ — Forecast Center
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getForecastableColumns, generateForecast } from '../lib/api'
import { TrendingUp, Calendar } from 'lucide-react'
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, ComposedChart, Legend } from 'recharts'
import type { SafeAny } from '../types'

interface Props {
  datasetId: string | null
}

export default function ForecastCenter({ datasetId }: Props) {
  const [selectedMetric, setSelectedMetric] = useState<string | undefined>()
  const [selectedDateCol, setSelectedDateCol] = useState<string | undefined>()

  const { data: forecastable, isLoading: colsLoading } = useQuery({
    queryKey: ['forecastable', datasetId],
    queryFn: () => getForecastableColumns(datasetId!),
    enabled: !!datasetId,
  })

  const { data: forecast, isLoading: forecastLoading } = useQuery({
    queryKey: ['forecast', datasetId, selectedMetric, selectedDateCol],
    queryFn: () => generateForecast(datasetId!, selectedMetric || '', '7,30,90', selectedDateCol),
    enabled: !!datasetId && (!!selectedMetric || (!!forecastable && (forecastable.forecastable?.length || 0) > 0)),
    retry: false
  })

  if (!datasetId) return <NoDataset label="Forecast Center" />

  if (colsLoading) return <LoadingState text="Analyzing time-series patterns..." />

  if (!forecastable?.forecastable?.length && !forecastable?.date_like_columns?.length && !selectedDateCol) {
    return (
      <div className="text-center py-20 animate-fade-in">
        <Calendar size={48} style={{ color: 'var(--color-text-muted)', margin: '0 auto 1rem' }} />
        <h2 className="font-bold text-xl mb-2" style={{ color: 'var(--color-text-primary)' }}>No Temporal Data Detected</h2>
        <p style={{ color: 'var(--color-text-secondary)' }}>
          Time-series forecasting requires a dataset with a date/time column and numeric metrics that change over time.
        </p>
      </div>
    )
  }

  // Handle fallback where we only found "date-like" columns
  if (!forecastable?.forecastable?.length && (forecastable?.date_like_columns?.length || 0) > 0 && !selectedDateCol) {
    return (
      <div className="text-center py-20 animate-fade-in max-w-lg mx-auto">
        <Calendar size={48} style={{ color: 'var(--color-text-muted)', margin: '0 auto 1rem' }} />
        <h2 className="font-bold text-xl mb-2" style={{ color: 'var(--color-text-primary)' }}>No Strict Date Column Detected</h2>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: '1.5rem' }}>
          We found some columns that might contain temporal data. Please select one to attempt forecasting:
        </p>
        <div className="flex flex-col gap-3">
          {forecastable?.date_like_columns?.map((col: string) => (
            <button 
              key={col}
              onClick={() => setSelectedDateCol(col)}
              className="px-4 py-2 border rounded-md hover:bg-slate-50 transition-colors font-medium text-slate-700"
              style={{ borderColor: 'var(--color-border)' }}
            >
              Use "{col}" as Time Axis
            </button>
          ))}
        </div>
      </div>
    )
  }
  
  if (forecastLoading && !forecast) return <LoadingState text="Generating multi-model forecasts..." />
  if (!forecast && !forecastLoading) return <div className="text-center py-20">Failed to generate forecast with selected parameters.</div>

  // Use the API response metric if user hasn't selected one
  const currentMetric = selectedMetric || forecast?.metric || (forecastable?.forecastable?.[0] || '')
  
  // Combine historical and forecast data for the chart
  const activeForecast = forecast?.forecasts?.find((f: SafeAny) => f.horizon_days === 30) // Default to 30 day view
  
  let chartData: Record<string, SafeAny>[] = []
  if (activeForecast) {
    const hist = activeForecast.historical.map((d: SafeAny) => ({
      date: d.date,
      Actual: d.value,
      Forecast: null,
      range: null
    }))
    const fut = activeForecast.forecast.map((d: SafeAny) => ({
      date: d.date,
      Actual: null,
      Forecast: d.value,
      range: [d.lower_bound, d.upper_bound]
    }))
    chartData = [...hist, ...fut]
  }

  return (
    <div className="animate-fade-in">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">Forecast Center</h1>
          <p className="page-subtitle">Predictive analytics with confidence intervals</p>
        </div>
        <div className="flex items-center gap-4">
          <select 
            value={currentMetric} 
            onChange={e => setSelectedMetric(e.target.value)}
            className="border rounded-md px-3 py-1.5 text-sm font-medium"
            style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
          >
            {forecastable?.forecastable?.map((c: string) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
      </div>

      {forecastLoading ? (
        <LoadingState text="Generating multi-model forecasts..." />
      ) : activeForecast ? (
        <>
          <div className="card card-body mb-6">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h3 className="font-bold text-lg mb-1" style={{ color: 'var(--color-text-primary)' }}>
                  30-Day Outlook: {currentMetric}
                </h3>
                <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                  {activeForecast.interpretation}
                </p>
              </div>
              <div className="flex gap-2">
                <span className="badge badge-info">{(activeForecast.model_used || '').replace('_', ' ').toUpperCase()}</span>
                <span className="badge" style={{ background: 'var(--color-surface-hover)' }}>
                  {(activeForecast.confidence_level || 0).toFixed(0)}% Confidence
                </span>
              </div>
            </div>

            <div style={{ height: 400, width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94A3B8' }} minTickGap={30} />
                  <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} domain={['auto', 'auto']} />
                  <Tooltip 
                    contentStyle={{ borderRadius: 12, border: '1px solid #E2E8F0', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                    labelStyle={{ fontWeight: 'bold', color: '#0F172A', marginBottom: 4 }}
                  />
                  <Legend wrapperStyle={{ paddingTop: 20 }} />
                  
                  {/* Confidence Interval Area */}
                  <Area type="monotone" dataKey="range" fill="#DBEAFE" stroke="none" name="Confidence Interval" />
                  
                  {/* Lines */}
                  <Line type="monotone" dataKey="Actual" stroke="#0F172A" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="Forecast" stroke="#2563EB" strokeWidth={2.5} strokeDasharray="5 5" dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Model Performance Validation Metrics */}
          {activeForecast.metrics && (
            <div className="card card-body mb-6 border border-slate-200">
              <h4 className="font-bold text-xs uppercase tracking-wider text-slate-400 mb-3">
                Best Fit Model Evaluation Summary (80/20 Validation Split)
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Model Selected</span>
                  <div className="text-base font-extrabold text-slate-800 mt-1 capitalize">
                    {activeForecast.model_used.replace('_', ' ')}
                  </div>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Mean Absolute Error (MAE)</span>
                  <div className="text-base font-extrabold text-slate-800 mt-1">
                    {activeForecast.metrics.mae?.toLocaleString() || 'N/A'}
                  </div>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400">MAPE</span>
                  <div className="text-base font-extrabold text-slate-800 mt-1">
                    {activeForecast.metrics.mape !== undefined ? `${activeForecast.metrics.mape}%` : 'N/A'}
                  </div>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Coefficient of Determination (R²)</span>
                  <div className="text-base font-extrabold text-slate-800 mt-1">
                    {activeForecast.metrics.r_squared !== undefined ? activeForecast.metrics.r_squared.toFixed(3) : 'N/A'}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {forecast?.forecasts?.map((f: SafeAny, i: number) => (
              <ForecastMetricCard key={i} forecast={f} />
            ))}
          </div>
        </>
      ) : null}
    </div>
  )
}

function ForecastMetricCard({ forecast }: { forecast: SafeAny }) {
  const lastHist = forecast.historical[forecast.historical.length - 1]?.value || 0
  const lastFore = forecast.forecast[forecast.forecast.length - 1]?.value || 0
  const pctChange = ((lastFore - lastHist) / Math.abs(lastHist || 1)) * 100
  const isUp = pctChange > 0

  return (
    <div className="card card-body">
      <div className="text-sm font-semibold mb-4 text-center" style={{ color: 'var(--color-text-secondary)' }}>
        {forecast.horizon_days} Day Forecast
      </div>
      <div className="text-center mb-4">
        <div className="text-3xl font-extrabold mb-1" style={{ color: 'var(--color-text-primary)' }}>
          {lastFore > 1000 ? `${(lastFore/1000).toFixed(1)}k` : lastFore.toFixed(2)}
        </div>
        <div className="text-sm font-medium" style={{ color: isUp ? 'var(--color-success)' : 'var(--color-danger)' }}>
          {isUp ? '↑' : '↓'} {Math.abs(pctChange).toFixed(1)}% vs today
        </div>
      </div>
      <div className="text-xs text-center" style={{ color: 'var(--color-text-muted)' }}>
        Expected range: {forecast.forecast[forecast.forecast.length - 1]?.lower_bound?.toFixed(0)} - {forecast.forecast[forecast.forecast.length - 1]?.upper_bound?.toFixed(0)}
      </div>
    </div>
  )
}

function NoDataset({ label }: { label: string }) {
  return (
    <div className="text-center py-20 animate-fade-in">
      <TrendingUp size={48} style={{ color: 'var(--color-text-muted)', margin: '0 auto 1rem' }} />
      <h2 className="font-bold text-xl mb-2" style={{ color: 'var(--color-text-primary)' }}>{label}</h2>
      <p style={{ color: 'var(--color-text-secondary)' }}>Upload a dataset to generate forecasts</p>
    </div>
  )
}

function LoadingState({ text }: { text: string }) {
  return (
    <div className="text-center py-20 animate-pulse">
      <div className="inline-block p-4 rounded-full mb-4" style={{ background: 'var(--color-primary-50)' }}>
        <TrendingUp size={32} style={{ color: 'var(--color-primary)' }} />
      </div>
      <h2 className="font-bold text-lg mb-2">{text}</h2>
      <div className="w-48 h-1 mx-auto rounded-full mt-4" style={{ background: 'var(--color-border-light)' }}>
        <div className="h-full rounded-full animate-pulse" style={{ width: '60%', background: 'var(--color-primary)' }} />
      </div>
    </div>
  )
}

