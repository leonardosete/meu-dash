import React, { useState, useEffect, useCallback } from 'react';
import { getDashboardSummary } from '../services/api';
import { DashboardSummary } from '../types';
import KpiCard from './KpiCard';
import HistoryPage from './HistoryPage'; // Importa o componente completo
import UploadForms from './UploadForms';
import KpiEarLinks from './KpiEarLinks'; // <-- 1. Importe o novo componente

const Dashboard = () => {
  const [summaryData, setSummaryData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getDashboardSummary();
      setSummaryData(data);
      setError(null);
    } catch (err) {
      setError('Falha ao carregar os dados do dashboard. O backend está no ar?');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    document.addEventListener('visibilitychange', fetchData);
    return () => document.removeEventListener('visibilitychange', fetchData);
  }, [fetchData]);

  const renderKpiContent = () => {
    if (loading) {
      return <div className="text-center p-10">Carregando dados do dashboard...</div>;
    }

    if (error) {
      return <div className="text-center p-10 text-red-400">{error}</div>;
    }
    
    if (!summaryData?.kpi_summary) {
      return null;
    }

    const { kpi_summary } = summaryData;
    
    const getSuccessColor = (rate: number) => {
      if (rate < 50) return 'text-danger';
      if (rate < 70) return 'text-warning';
      return 'text-success';
    };

    const successColorClass = getSuccessColor(kpi_summary.taxa_sucesso_valor);

    return (
      <div className="kpi-dashboard">
        <KpiCard
          title="Casos sem Remediação"
          value={kpi_summary.casos_atuacao}
          subValue={kpi_summary.alertas_atuacao}
          subLabel="Alertas"
          colorClass={kpi_summary.casos_atuacao > 0 ? 'text-danger' : 'text-success'}
        />
        <KpiCard
          title="Casos com Instabilidade"
          value={kpi_summary.casos_instabilidade}
          subValue={kpi_summary.alertas_instabilidade > 0 ? kpi_summary.alertas_instabilidade : undefined}
          subLabel={kpi_summary.alertas_instabilidade > 0 ? "Alertas" : undefined}
          colorClass={kpi_summary.casos_instabilidade > 0 ? 'text-warning' : 'text-success'}
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
      {summaryData && summaryData.kpi_summary && (
        <div className="card">
          {/* 2. Adicione o componente aqui, passando as URLs do kpi_summary */}
          <KpiEarLinks 
            reportUrl={summaryData.kpi_summary.report_url}
            actionPlanUrl={summaryData.kpi_summary.action_plan_url}
            trendAnalysisUrl={summaryData.kpi_summary.trend_analysis_url}
          />
          {renderKpiContent()}
        </div>
      )}
      
      <UploadForms onUploadSuccess={fetchData} />
    </>
  );
};

export default Dashboard;