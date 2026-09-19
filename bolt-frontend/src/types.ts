export interface User {
  id: number;
  name: string;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ReportSummary {
  report_id: number;
  report_name: string;
  summary: {
    normal_count: number;
    low_count: number;
    high_count: number;
    total_count: number;
  };
  biomarkers: Biomarker[];
  overall_summary: string | null;
}

export interface Biomarker {
  id: number;
  name: string;
  value: number;
  unit: string;
  ref_low: number;
  ref_high: number;
  status: 'LOW' | 'NORMAL' | 'HIGH';
  explanation: string | null;
}

export interface ReportListItem {
  id: number;
  report_name: string;
  report_date: string;
  upload_date: string;
  file_url: string;
}

export interface UploadResponse {
  message: string;
  report: ReportListItem;
}

export interface TrendPoint {
  report_id: number;
  report_date: string;
  value: number;
  status: 'LOW' | 'NORMAL' | 'HIGH';
}

export interface TrendResponse {
  name: string;
  unit: string;
  history: TrendPoint[];
  trend_summary: string | null;
}

export interface ApiError {
  detail: string;
}
