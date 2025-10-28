export interface KpiSummary {
  casos_atuacao: number;
  alertas_atuacao: number;
  casos_instabilidade: number;
  alertas_instabilidade: number;
  casos_sucesso_parcial: number;
  alertas_sucesso_parcial: number;
  taxa_sucesso_automacao: string;
  taxa_sucesso_valor: number;
  casos_sucesso: number;
  total_casos: number;
}

export interface TrendHistoryItem {
  run_folder: string;
  filename: string;
  url: string;
}

export interface ReportUrls {
  summary?: string;
  action_plan?: string;
  trend?: string;
}

export interface DashboardSummary {
  kpi_summary: KpiSummary | null;
  trend_history: TrendHistoryItem[];
  latest_report_urls: ReportUrls | null;
  quick_diagnosis_html?: string | null;
  latest_report_date_range?: string | null;
}

export interface UploadSuccessResponse {
  success: boolean;
  report_urls: ReportUrls;
  kpi_summary: KpiSummary | null;
  quick_diagnosis_html: string | null;
  date_range: string | null;
}

export interface Report {
  id: string; // ID can be 'standard-X' or 'comparative-Y'
  type: 'standard' | 'comparative';
  timestamp: string;
  original_filename: string;
  date_range: string;
  url: string;
}

export interface LoginCredentials {
  username?: string;
  password?: string;
}