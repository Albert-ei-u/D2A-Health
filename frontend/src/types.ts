export type Severity = "low" | "medium" | "high";

export interface Alert {
  id: string;
  title: string;
  severity: Severity;
  district: string;
  condition: string;
  message: string;
  confidence: number;
  evidence: string[];
}

export interface EnvironmentalSignal {
  district: string;
  week: string;
  rainfall_mm: number;
  temperature_c: number;
  air_quality_index: number;
}

export interface Insight {
  id: string;
  title: string;
  category: string;
  confidence: number;
  summary: string;
  considerations: string[];
  evidence: string[];
}

export interface DashboardSummary {
  total_visits: number;
  total_admissions: number;
  active_alerts: number;
  average_wait_minutes: number;
  top_conditions: Array<{ condition: string; visits: number }>;
  weekly_volume: Array<{ week: string; visits: number }>;
  environmental_context: EnvironmentalSignal[];
  alerts: Alert[];
  insights: Insight[];
}
