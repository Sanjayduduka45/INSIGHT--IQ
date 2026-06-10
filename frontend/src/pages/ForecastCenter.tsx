import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getForecastableColumns, generateForecast, logUserActivity } from '../lib/api'
import { TrendingUp, Calendar, Save, Share, AlertTriangle } from 'lucide-react'
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, ComposedChart, Legend } from 'recharts'
import type { SafeAny } from '../types'
import { useAuth } from '../lib/auth'


function safeRender(value: any): React.ReactNode {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }
  if (typeof value === 'object') {
    if (Array.isArray(value)) {
      return value.map((item, idx) => <span key={idx}>{safeRender(item)} </span>);
    }
    if ((value as any).$$typeof) {
      return value;
    }
    if ((value as any).message) return String((value as any).message);
    if ((value as any).error) return String((value as any).error);
    if ((value as any).name) return String((value as any).name);
    try {
      return JSON.stringify(value);
    } catch {
      return '[Object]';
    }
  }
  return String(value);
}

interface Props {
  datasetId: string | null
}

export default function ForecastCenter({ datasetId }: Props) {
  const { user } = useAuth()
  const [selectedMetric, setSelectedMetric] = useState<string | undefined>()
  const [selectedDateCol, setSelectedDateCol] = useState<string | undefined>()

  const handleShare = () => {
    if (user?.role === 'guest') {
      window.dispatchEvent(new CustomEvent('insightiq-trigger-signup'))
    } else {
      alert('Dashboard link copied to clipboard! (Share feature simulated)')
    }
  }

  const handleSaveProject = () => {
    if (user?.role === 'guest') {
      window.dispatchEvent(new CustomEvent('insightiq-trigger-signup'))
    } else {
      alert('Project saved successfully in the cloud! (Save feature simulated)')
    }
  }

  const { data: forecastable, isLoading: colsLoading, error: colsError } = useQuery({
    queryKey: ['forecastable', datasetId],
    queryFn: () => getForecastableColumns(datasetId!),
    enabled: !!datasetId,
  })

  const { data: forecast, isLoading: forecastLoading, error: forecastError } = useQuery({
    queryKey: ['forecast', datasetId, selectedMetric, selectedDateCol],
    queryFn: async () => {
      const res = await generateForecast(datasetId!, selectedMetric || '', '7,30,90', selectedDateCol)
      if (res && res.metric) {
        logUserActivity('AI Forecast Run', `${res.metric} [${res.date_column || 'Time'}]`)
      }
      return res
    },
    enabled: !!datasetId && (!!selectedMetric || (!!forecastable && (forecastable.forecastable?.length || 0) > 0)),
    retry: false
  })

  if (!datasetId) return <NoDataset label="Forecast Center" />

  if (colsLoading) return <LoadingState text="Analyzing time-series patterns..." />

  if (colsError || forecastError) {
    const err = (colsError || forecastError) as any;
    return (
      <div className="max-w-2xl mx-auto py-16 animate-fade-in">
        <div className="card card-body border-red-200 bg-red-50/10">
          <div className="flex items-center gap-3 text-red-600 mb-4">
            <AlertTriangle size={32} />
            <h3 className="text-lg font-bold">Forecasting Error</h3>
          </div>
          <p className="text-sm text-slate-700 mb-6 font-medium">
            {err?.message || "An unexpected error occurred while communicating with the forecasting service."}
          </p>
        </div>
      </div>
    )
  }

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
  
  const forecastAny = forecast as any;
  const hasForecast = forecastAny && forecastAny.status !== 'failed' && forecastAny.forecasts && forecastAny.forecasts.length > 0;

  if (!hasForecast && !forecastLoading) {
    const reason = forecastAny?.reason || "The selected time-series data points are insufficient (minimum 10 rows required) after grouping, or the data values are constant/blank.";
    const required = forecastAny?.required_fields || [
      "At least 10 historical chronological records",
      "Continuous numerical metric values (non-constant variance)"
    ];
    return (
      <div className="max-w-2xl mx-auto py-16 animate-fade-in">
        <div className="card card-body border-slate-200">
          <div className="flex items-center gap-3 text-amber-600 mb-4">
            <Calendar size={32} />
            <h3 className="text-lg font-bold">Forecasting Model Constraints</h3>
          </div>
          <p className="text-sm text-slate-600 mb-6 font-medium">
            {safeRender(reason)}
          </p>
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
              Required Fields & Verification Checklist:
            </h4>
            <ul className="space-y-2">
              {required.map((req: string, idx: number) => (
                <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-600">
                  <span className="text-blue-500 font-bold">•</span>
                  <span>{safeRender(req)}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    )
  }

  // Use the API response metric if user hasn't selected one
  const firstCol = forecastable?.forecastable?.[0];
  const defaultMetric = typeof firstCol === 'string' ? firstCol : firstCol?.column;
  const currentMetric = selectedMetric || forecast?.metric || (defaultMetric || '')
  
  // Combine historical and forecast data for the chart
  const activeForecast = forecast?.forecasts?.find((f: SafeAny) => f.horizon_days === 30) // Default to 30 day view
  
  let chartData: Record<string, SafeAny>[] = []
  if (activeForecast) {
    const hist = activeForecast.historical.map((d: SafeAny) => ({
      date: d.date,
      Actual: d.value,
      Forecast: null,
      range: [d.value, d.value]
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
      <div className="page-header flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="page-title">Forecast Center</h1>
          <p className="page-subtitle">Predictive analytics with confidence intervals</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <select 
            value={currentMetric} 
            onChange={e => setSelectedMetric(e.target.value)}
            className="border rounded-xl px-3 py-2 text-sm font-semibold text-slate-700 bg-white dark:bg-slate-800 dark:text-white"
            style={{ borderColor: 'var(--color-border)' }}
          >
            {forecastable?.forecastable?.map((c: SafeAny) => {
              const columnName = typeof c === 'string' ? c : c?.column;
              return (
                <option key={columnName} value={columnName}>
                  {columnName}
                </option>
              );
            })}
          </select>

          <button 
            onClick={handleSaveProject}
            className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 rounded-xl font-semibold text-sm shadow-sm transition-all text-slate-700 dark:text-white cursor-pointer"
          >
            <Save size={16} />
            Save Project
          </button>

          <button 
            onClick={handleShare}
            className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 rounded-xl font-semibold text-sm shadow-sm transition-all text-slate-700 dark:text-white cursor-pointer"
          >
            <Share size={16} />
            Share Dashboard
          </button>
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
                  30-Day Outlook: {safeRender(currentMetric)}
                </h3>
                <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                  {safeRender(activeForecast.interpretation)}
                </p>
              </div>
              <div className="flex gap-2">
                <span className="badge badge-info">{safeRender((activeForecast.model_used || '').replace('_', ' ').toUpperCase())}</span>
                <span className="badge" style={{ background: 'var(--color-surface-hover)' }}>
                  {safeRender((activeForecast.confidence_level || 0).toFixed(0))}% Confidence
                </span>
              </div>
            </div>

            <div className="h-[260px] sm:h-[400px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94A3B8' }} minTickGap={30} />
                  <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} domain={['auto', 'auto']} />
                  <Tooltip 
                    contentStyle={{ borderRadius: 12, border: '1px solid #E2E8F0', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                    labelStyle={{ fontWeight: 'bold', color: '#0F172A', marginBottom: 4 }}
                    formatter={(value: any, name: any) => {
                      if (name === 'Confidence Interval') {
                        if (Array.isArray(value)) {
                          if (value[0] === value[1] || value[0] == null || value[1] == null) return ['', name];
                          return [`${Number(value[0]).toFixed(2)} - ${Number(value[1]).toFixed(2)}`, name];
                        }
                        return ['', name];
                      }
                      if (value == null) return ['', name];
                      return [value, name];
                    }}
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
                    {safeRender((activeForecast.model_used || '').replace('_', ' '))}
                  </div>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Mean Absolute Error (MAE)</span>
                  <div className="text-base font-extrabold text-slate-800 mt-1">
                    {safeRender(activeForecast.metrics.mae?.toLocaleString() || 'N/A')}
                  </div>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400">MAPE</span>
                  <div className="text-base font-extrabold text-slate-800 mt-1">
                    {safeRender(activeForecast.metrics.mape !== undefined ? `${activeForecast.metrics.mape}%` : 'N/A')}
                  </div>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Coefficient of Determination (R²)</span>
                  <div className="text-base font-extrabold text-slate-800 mt-1">
                    {safeRender(activeForecast.metrics.r_squared !== undefined ? activeForecast.metrics.r_squared.toFixed(3) : 'N/A')}
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
        {safeRender(forecast.horizon_days)} Day Forecast
      </div>
      <div className="text-center mb-4">
        <div className="text-3xl font-extrabold mb-1" style={{ color: 'var(--color-text-primary)' }}>
          {safeRender(lastFore > 1000 ? `${(lastFore/1000).toFixed(1)}k` : lastFore.toFixed(2))}
        </div>
        <div className="text-sm font-medium" style={{ color: isUp ? 'var(--color-success)' : 'var(--color-danger)' }}>
          {isUp ? '↑' : '↓'} {safeRender(Math.abs(pctChange).toFixed(1))}% vs today
        </div>
      </div>
      <div className="text-xs text-center" style={{ color: 'var(--color-text-muted)' }}>
        Expected range: {safeRender(forecast.forecast[forecast.forecast.length - 1]?.lower_bound?.toFixed(0))} - {safeRender(forecast.forecast[forecast.forecast.length - 1]?.upper_bound?.toFixed(0))}
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

