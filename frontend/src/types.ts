export interface KpiSummary {
  casos_atuacao: number;
  alertas_atuacao: number;
  casos_instabilidade: number;
  alertas_instabilidade: number;
  taxa_sucesso_automacao: string;
  taxa_sucesso_valor: number;
  casos_sucesso: number;
  total_casos: number;
  report_url?: string;
}

export interface TrendHistoryItem {
  run_folder: string;
  filename: string;
  url: string;
}

export interface DashboardSummary {
  kpi_summary: KpiSummary | null;
  last_action_plan: { url: string } | null;
  last_report_info: { run_folder: string; filename: string } | null;
  trend_history: TrendHistoryItem[];
}