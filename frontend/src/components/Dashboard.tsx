import React, { useState, useEffect, useCallback } from "react";
import { getDashboardSummary } from "../services/api";
import { DashboardSummary, ReportUrls, UploadSuccessResponse } from "../types";
import KpiCard from "./KpiCard";
import UploadForms from "./UploadForms";
import WelcomeEmptyState from "./WelcomeEmptyState";
import ReportPreviews from "./ReportPreviews";
import { useDashboard } from "../hooks/useDashboard";

const Dashboard = () => {
  const [summaryData, setSummaryData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { reportUrls, setReportUrls, quickDiagnosis, setQuickDiagnosis } =
    useDashboard();
  const [dateRange, setDateRange] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getDashboardSummary();
      setSummaryData(data);
      if (data.latest_report_urls) {
        setReportUrls(data.latest_report_urls);
        setDateRange(data.latest_report_date_range || null);
      }
      if (data.quick_diagnosis_html) {
        setQuickDiagnosis(data.quick_diagnosis_html);
      }
      setError(null);
    } catch (err) {
      setError(
        "Falha ao carregar os dados do dashboard. O backend está no ar?",
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [setReportUrls, setQuickDiagnosis]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleUploadSuccess = (data: UploadSuccessResponse) => {
    setSummaryData((prev) => ({ ...prev!, kpi_summary: data.kpi_summary }));
    setReportUrls(data.report_urls);
    setQuickDiagnosis(data.quick_diagnosis_html);
    setDateRange(data.date_range);
  };

  const renderKpiContent = () => {
    if (loading) {
      return (
        <div className="text-center p-10">Carregando dados do dashboard...</div>
      );
    }

    if (error) {
      return <div className="text-center p-10 text-red-400">{error}</div>;
    }

    if (!summaryData?.kpi_summary) {
      return <WelcomeEmptyState />;
    }

    const { kpi_summary } = summaryData;

    const getSuccessColor = (rate: number) => {
      if (rate < 50) return "text-danger";
      if (rate < 70) return "text-warning";
      return "text-success";
    };

    const successColorClass = getSuccessColor(kpi_summary.taxa_sucesso_valor);

    return (
      <div className="kpi-dashboard">
        <KpiCard
          title="Casos sem Remediação"
          value={kpi_summary.casos_atuacao}
          subValue={
            kpi_summary.casos_atuacao > 0
              ? kpi_summary.alertas_atuacao
              : undefined
          }
          subLabel={kpi_summary.casos_atuacao > 0 ? "Alertas" : undefined}
          colorClass={
            kpi_summary.casos_atuacao > 0 ? "text-danger" : "text-success"
          }
        />
        <KpiCard
          title="Casos Remediados com Frequência"
          value={kpi_summary.casos_instabilidade}
          subValue={
            kpi_summary.alertas_instabilidade > 0
              ? kpi_summary.alertas_instabilidade
              : undefined
          }
          subLabel={
            kpi_summary.alertas_instabilidade > 0 ? "Alertas" : undefined
          }
          colorClass={
            kpi_summary.casos_instabilidade > 0
              ? "text-warning"
              : "text-success"
          }
        />
        <KpiCard
          title="Pontos de Atenção"
          value={kpi_summary.casos_sucesso_parcial}
          subValue={
            kpi_summary.alertas_sucesso_parcial > 0
              ? kpi_summary.alertas_sucesso_parcial
              : undefined
          }
          subLabel={
            kpi_summary.alertas_sucesso_parcial > 0 ? "Alertas" : undefined
          }
          colorClass={
            kpi_summary.casos_sucesso_parcial > 0
              ? "text-warning"
              : "text-success"
          }
        />
        <KpiCard
          title="Sucesso da Automação"
          value={kpi_summary.taxa_sucesso_automacao}
          subValue={`${kpi_summary.casos_sucesso} de ${kpi_summary.total_casos} Casos`}
          colorClass={successColorClass}
        />
      </div>
    );
  };

  return (
    <>
      <div className="kpi-section">{renderKpiContent()}</div>

      <div className="form-section-container">
        {reportUrls ? (
          <ReportPreviews
            key="previews"
            urls={reportUrls}
            quickDiagnosis={quickDiagnosis}
            dateRange={dateRange}
          />
        ) : (
          <div key="forms" className="page-fade-in">
            <UploadForms onUploadSuccess={handleUploadSuccess} />
          </div>
        )}
      </div>
    </>
  );
};

export default Dashboard;