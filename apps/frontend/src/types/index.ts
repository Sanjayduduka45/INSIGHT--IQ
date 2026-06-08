// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type SafeAny = any;

export interface KPI {
  name: string;
  value: number | string;
  trend: 'up' | 'down' | 'flat' | string;
  trend_value?: string | number;
  format?: string;
  icon?: string | SafeAny;
  formatted_value?: string;
  [key: string]: SafeAny;
}

export interface Insight {
  type: 'positive' | 'warning' | 'info' | 'neutral' | string;
  title: string;
  description: string;
  severity?: string;
  [key: string]: SafeAny;
}

export interface Anomaly {
  severity: 'critical' | 'high' | 'medium' | 'low' | string;
  method: string;
  explanation: string;
  business_impact: string;
  recommendation: string;
  values: Record<string, string | number | SafeAny>;
  [key: string]: SafeAny;
}

export interface Forecast {
  horizon_days: number;
  historical: { date: string; value: number; lower_bound?: number; upper_bound?: number }[];
  forecast: { date: string; value: number; lower_bound?: number; upper_bound?: number }[];
  metric?: string;
  interpretation?: string;
  model_used?: string;
  confidence_level?: number;
  [key: string]: SafeAny;
}

export interface Chart {
  type: string;
  title: string;
  data: SafeAny[];
  x_axis?: string;
  y_axis?: string;
  columns?: string[];
  [key: string]: SafeAny;
}

export interface DatasetDomain {
  name: string;
  confidence: number;
  [key: string]: SafeAny;
}

export interface DatasetQuality {
  grade: string;
  score: number;
  issues: string[];
  [key: string]: SafeAny;
}

export interface OverviewData {
  dataset_name?: string;
  kpis?: KPI[];
  quick_stats?: Record<string, number | string | SafeAny>;
  domain?: DatasetDomain;
  health_scores?: Record<string, number | string | SafeAny>;
  growth?: number | string | { growth_rate: number; status: string };
  growth_rate?: number | string | { growth_rate: number; status: string };
  performers?: TopPerformersData | SafeAny;
  root_cause_summary?: string;
  ai_recommendations?: string[];
  insights?: Insight[];
  executive_intelligence?: SafeAny;
}

export interface TopPerformersData {
  products?: { name: string; value: number }[];
  customers?: { name: string; value: number }[];
  categories?: { name: string; value: number }[];
  regions?: { name: string; value: number }[];
  [key: string]: SafeAny;
}