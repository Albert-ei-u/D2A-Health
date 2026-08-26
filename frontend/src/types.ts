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

export interface DiseaseTrend {
  district: string;
  condition: string;
  total_visits: number;
  latest_week_visits: number;
  week_over_week_change_percent: number;
  overall_change_percent: number;
  trend: "rising" | "stable" | "falling";
}

export interface PatientVolumeAnalysis {
  district: string;
  total_visits: number;
  latest_week_visits: number;
  average_weekly_visits: number;
  week_over_week_change_percent: number;
  admissions: number;
  admission_rate_percent: number;
  average_wait_minutes: number;
  pressure_level: "low" | "medium" | "high";
}

export interface AnomalySignal {
  district: string;
  condition: string;
  week: string;
  current_visits: number;
  baseline_visits: number;
  absolute_change: number;
  percent_change: number;
  z_score: number;
  score: number;
  is_significant: boolean;
}

export interface DashboardSummary {
  total_visits: number;
  total_admissions: number;
  active_alerts: number;
  average_wait_minutes: number;
  top_conditions: Array<{ condition: string; visits: number }>;
  weekly_volume: Array<{ week: string; visits: number }>;
  disease_trends: DiseaseTrend[];
  patient_volume_analysis: PatientVolumeAnalysis[];
  anomaly_signals: AnomalySignal[];
  environmental_context: EnvironmentalSignal[];
  alerts: Alert[];
  insights: Insight[];
}
