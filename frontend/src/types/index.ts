export interface TopPredictionItem {
  rank: number;
  class_name: string;
  display_name: string;
  score: number;
  percentage: number;
}

export interface ImageAnalysisView {
  view: 'front' | 'left' | 'right';
  label: string;
  predicted_class: string;
  model_output_score: number;
  confidence?: number; // Backwards compatibility
  confidence_percentage: number;
  is_abstaining: boolean;
  is_inconclusive?: boolean; // Backwards compatibility
  processing_status: string;
  inference_time_ms: number;
  top_three_predictions: TopPredictionItem[];
  model_output_scores: Record<string, number>;
  original_image?: string | null;
  heatmap_image?: string | null;
  annotated_image?: string | null; // Backwards compatibility
  gradcam_salience_stats?: {
    mean_activation?: number;
    peak_activation?: number;
    high_salience_area_percentage?: number;
  };
  gradcam_explanation?: string;
  category?: string;
  clinical_signs?: string[];
  clinical_relevance?: string;
}

export interface ConditionDetectedItem {
  disease_key: string;
  disease_name: string;
  category?: string;
  affected_views: string[];
  scores_by_view: Record<string, number>;
  peak_score: number;
  clinical_signs: string[];
  clinical_relevance?: string;
  // Backwards compatibility
  severity?: string;
  confidence_percentage?: number;
  peak_confidence?: number;
}

export interface ScreeningSummary {
  overall_status: string;
  triage_recommendation?: string;
  urgency_level?: string; // Backwards compatibility
  narrative: string;
  abstained_views: string[];
  has_abstained_views?: boolean;
  inconclusive_views?: string[];
  multi_view_notice?: string;
}

export interface PatientInfo {
  id?: number;
  patient_id: string;
  name: string;
  age?: number | null;
  date_of_birth?: string | null;
  gender?: string;
  contact_number?: string | null;
  email?: string | null;
  medical_history?: string | null;
  dental_history?: string | null;
  notes?: string;
  created_at?: string;
  updated_at?: string;
  analyses_count?: number;
}

export interface ReportDetail {
  report_id: string;
  scan_date: string;
  scan_date_iso: string;
  total_inference_time_ms?: number;
  patient: PatientInfo;
  screening_summary: ScreeningSummary;
  conditions_detected?: ConditionDetectedItem[];
  detected_conditions?: any[]; // Backwards compatibility
  images_analyzed: ImageAnalysisView[];
  recommended_examination_steps?: string[];
  clinical_recommendations?: string[]; // Backwards compatibility
  primary_safety_notice?: string;
  disclaimer: string;
}

export interface AnalysisSummary {
  analysis_id: string;
  report_id: string;
  patient_id: string;
  patient_name: string;
  overall_status: string;
  urgency_level: string;
  created_at: string;
  findings_count: number;
}

export interface DashboardStats {
  total_patients: number;
  total_scans: number;
  completed_scans: number;
  inconclusive_scans: number;
  disease_distribution: Record<string, number>;
  urgency_distribution: Record<string, number>;
  recent_analyses: AnalysisSummary[];
  scans_over_time?: Array<{ date: string; scans: number }>;
}

export interface HealthStatus {
  status: string;
  ai_model_loaded: boolean;
  database_status: string;
  database_type: string;
  supported_classes: string[];
  timestamp: string;
}

export interface ModelStatusResponse {
  is_loaded: boolean;
  file_exists: boolean;
  model_path: string;
  architecture: string;
  input_shape: (number | null)[];
  output_shape: (number | null)[];
  num_classes: number;
  classes: string[];
  class_mapping: Record<string, string>;
  gradcam_layer: string;
  abstention_threshold: number;
  model_size_mb: number;
  primary_safety_notice: string;
  timestamp: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'dentist' | 'staff';
  full_name: string;
  is_active?: boolean;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface AuditLogItem {
  id: number;
  username?: string | null;
  action: string;
  resource_type?: string | null;
  resource_id?: string | null;
  ip_address?: string | null;
  status_code?: number | null;
  created_at: string;
}
