import type {
  OverviewData,
  KPI,
  Anomaly,
  Forecast,
  Chart,
  Insight,
  SafeAny,
} from '../types';

// Centralized API URL using environment variable or defaulting to same-host /api
const API_URL = import.meta.env.VITE_API_URL || '';
const API_BASE = `${API_URL}/api`;

export class ApiError extends Error {
  status: number;
  diagnostics?: Record<string, any> | null;
  constructor(status: number, message: string, diagnostics?: Record<string, any> | null) {
    super(message);
    this.status = status;
    this.diagnostics = diagnostics || null;
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const token = localStorage.getItem('insightiq_token');
  const headers = new Headers(options?.headers || {});
  headers.set('Content-Type', 'application/json');
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = body.detail;
    if (detail && typeof detail === 'object') {
      throw new ApiError(res.status, detail.message || 'Request failed', detail.diagnostics);
    }
    throw new ApiError(res.status, detail || res.statusText);
  }

  return res.json();
}

// ── Dataset APIs ────────────────────────────────────────────────────────

export async function uploadDataset(file: File) {
  const form = new FormData();
  form.append('file', file);

  const token = localStorage.getItem('insightiq_token');
  const headers = new Headers();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const res = await fetch(`${API_BASE}/datasets/upload`, {
    method: 'POST',
    body: form,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = body.detail;
    if (detail && typeof detail === 'object') {
      throw new ApiError(res.status, detail.message || 'Upload failed', detail.diagnostics);
    }
    throw new ApiError(res.status, detail || 'Upload failed');
  }

  return res.json();
}

export const listDatasets = () => request<Record<string, unknown>[]>('/datasets/list');
export const getDataset = (id: string) => request<Record<string, unknown>>(`/datasets/${id}`);
export const getDatasetPreview = (id: string, rows = 100) =>
  request<Record<string, unknown>>(`/datasets/${id}/preview?rows=${rows}`);
export const deleteDataset = (id: string) =>
  request<Record<string, unknown>>(`/datasets/${id}`, { method: 'DELETE' });
export const updateDatasetContext = (
  id: string,
  context: { business_problem: string; analysis_goal: string; success_metric: string }
) =>
  request<{ status: string; context: Record<string, string> }>(`/datasets/${id}/context`, {
    method: 'POST',
    body: JSON.stringify(context),
  });

// ── Analytics APIs ──────────────────────────────────────────────────────

export const getOverview = (datasetId: string) =>
  request<OverviewData>(`/analytics/${datasetId}/overview`);

export const getKPIs = (datasetId: string) =>
  request<{ dataset_id: string; domain: string; kpis: KPI[] }>(`/analytics/${datasetId}/kpis`);

export const getTrends = (datasetId: string, dateCol?: string, metricCols?: string) => {
  let query = '';
  if (dateCol || metricCols) {
    const params = new URLSearchParams();
    if (dateCol) params.append('date_col', dateCol);
    if (metricCols) params.append('metric_cols', metricCols);
    query = `?${params.toString()}`;
  }
  return request<{ dataset_id: string; date_column: string; trends: SafeAny[] }>(
    `/analytics/${datasetId}/trends${query}`
  );
};

export const getTopPerformers = (datasetId: string, dimension?: string, metric?: string) => {
  let query = '';
  if (dimension || metric) {
    const params = new URLSearchParams();
    if (dimension) params.append('dimension', dimension);
    if (metric) params.append('metric', metric);
    query = `?${params.toString()}`;
  }
  return request<{ dimension: string; metric: string; items: SafeAny[] }>(
    `/analytics/${datasetId}/top-performers${query}`
  );
};

export const getCorrelations = (datasetId: string, method = 'pearson') =>
  request<{ dataset_id: string; numeric_columns: string[]; correlation_matrix: number[][]; top_correlations: SafeAny[] }>(
    `/analytics/${datasetId}/correlations?method=${method}`
  );

export const getDistributions = (datasetId: string) =>
  request<{ dataset_id: string; distributions: Record<string, SafeAny> }>(
    `/analytics/${datasetId}/distributions`
  );

export const getCustomerIntelligence = (datasetId: string) =>
  request<SafeAny>(`/analytics/${datasetId}/customer-intelligence`);

// ── Anomaly APIs ────────────────────────────────────────────────────────

export const detectAnomalies = (datasetId: string, contamination = 0.05, methods?: string) => {
  let query = `?contamination=${contamination}`;
  if (methods) query += `&methods=${methods}`;
  return request<{
    dataset_id: string;
    total_records: number;
    total_anomalies: number;
    anomaly_rate: number;
    severity_breakdown: Record<string, number>;
    column_anomaly_counts: Record<string, number>;
    summary: string;
    anomalies: Anomaly[];
  }>(`/anomalies/${datasetId}/detect${query}`);
};

// ── Forecasting APIs ────────────────────────────────────────────────────

export const getForecastableColumns = (datasetId: string) =>
  request<{ dataset_id: string; date_column?: string; forecastable: any[]; date_like_columns: string[] }>(
    `/forecasting/${datasetId}/forecastable`
  );

export const generateForecast = (datasetId: string, metric: string, horizons = '7,30,90', dateColumn?: string) => {
  let query = `?metric=${metric}&horizons=${horizons}`;
  if (dateColumn) query += `&date_column=${dateColumn}`;
  return request<{
    dataset_id: string;
    metric: string;
    date_column: string;
    forecasts: Forecast[];
  }>(`/forecasting/${datasetId}/generate${query}`);
};

// ── Chat APIs ───────────────────────────────────────────────────────────

export const sendChatMessage = (datasetId: string, message: string, conversationId?: string) =>
  request<{
    response: string;
    charts: Chart[];
    insights: Insight[];
    suggested_questions: string[];
    sources: string[];
  }>('/chat/', {
    method: 'POST',
    body: JSON.stringify({
      dataset_id: datasetId,
      message,
      conversation_id: conversationId,
    }),
  });

// ── Export APIs ─────────────────────────────────────────────────────────

export const getExportUrl = (datasetId: string, format: 'pdf' | 'ppt' | 'csv' | 'xlsx') => {
  return `${API_BASE}/export/${datasetId}/${format}`;
};

// ── Settings APIs ───────────────────────────────────────────────────────

export const getInfrastructureStatus = () =>
  request<{
    ai: { provider: string; connected: boolean; status: string };
    database: { provider: string; connected: boolean; status: string };
    storage: { provider: string; connected: boolean; status: string };
  }>('/settings/infrastructure');

export const testConnection = (service: string) =>
  request<{ status: 'success' | 'error'; message: string }>('/settings/test-connection', {
    method: 'POST',
    body: JSON.stringify({ service }),
  });

export const getCharts = (datasetId: string, dashboard?: string) => {
  const query = dashboard ? `?dashboard=${dashboard}` : '';
  return request<{ dataset_id: string; charts: Chart[] }>(`/analytics/${datasetId}/charts${query}`);
};

export const getRootCauses = (datasetId: string) =>
  request<{ dataset_id: string; root_causes: SafeAny[] }>(`/analytics/${datasetId}/root-cause`);

export const generateCustomChart = (datasetId: string, type: string, xAxis?: string, yAxis?: string) => {
  const params = new URLSearchParams({ type });
  if (xAxis) params.append('x_axis', xAxis);
  if (yAxis) params.append('y_axis', yAxis);
  return request<Chart>(`/analytics/${datasetId}/generate-custom-chart?${params.toString()}`, {
    method: 'POST',
  });
};

export interface UserActivity {
  event: string;
  asset: string;
  status: string;
  timestamp: string;
}

export function logUserActivity(event: string, asset: string) {
  try {
    const userJson = localStorage.getItem('insightiq_user');
    if (!userJson) return;
    const user = JSON.parse(userJson);
    const email = user.email || 'unknown';
    const key = `insightiq_activity_${email}`;

    const existing = localStorage.getItem(key);
    const list: UserActivity[] = existing ? JSON.parse(existing) : [];

    const newActivity: UserActivity = {
      event,
      asset,
      status: 'Success',
      timestamp: new Date().toISOString(),
    };

    // Filter duplicates within a 5-second window to prevent double logging from React strict mode
    if (list.length > 0) {
      const last = list[0];
      const timeDiff = new Date().getTime() - new Date(last.timestamp).getTime();
      if (last.event === event && last.asset === asset && timeDiff < 5000) {
        return;
      }
    }

    list.unshift(newActivity);
    localStorage.setItem(key, JSON.stringify(list.slice(0, 10)));
  } catch (err) {
    console.error('Failed to log user activity:', err);
  }
}

export function getUserActivities(): UserActivity[] {
  try {
    const userJson = localStorage.getItem('insightiq_user');
    if (!userJson) return [];
    const user = JSON.parse(userJson);
    const email = user.email || 'unknown';
    const key = `insightiq_activity_${email}`;
    const existing = localStorage.getItem(key);
    return existing ? JSON.parse(existing) : [];
  } catch (err) {
    console.error('Failed to read user activities:', err);
    return [];
  }
}