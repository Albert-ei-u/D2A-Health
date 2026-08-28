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
  role_actions?: Record<string, string[]>;
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
  active_data_source?: string;
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
  district_forecasts: Array<{ district: string; next_week: string; current_visits: number; predicted_visits: number; lower_bound: number; upper_bound: number; trend_direction: string; confidence: number }>;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    email: string;
    name: string;
    role: string;
    health_center: string;
    dataset_ready: boolean;
  };
  name: string;
  role: string;
  email: string;
  health_center: string;
  requires_data_upload: boolean;
}

export interface SignupResponse {
  message: string;
  verification_required: boolean;
  development_code?: string;
}

export interface IngestionResult {
  accepted_records: number;
  rejected_records: number;
  records: Array<Record<string, unknown>>;
  errors: string[];
  active_data_source: string;
}

export interface PatientRecord {
  record_id: string;
  facility: string;
  district: string;
  village?: string;
  week: string;
  age_group: string;
  condition: string;
  visits: number;
  admissions: number;
  avg_wait_minutes: number;
  latitude?: number;
  longitude?: number;
}
