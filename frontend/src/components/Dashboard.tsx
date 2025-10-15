import React, { useState, useEffect, useCallback } from 'react';
import * as api from '../services/api';
import { LayoutDashboard } from 'lucide-react';
import { DashboardSummary } from '../types'; // Importa os tipos que criamos
import KpiCard from './KpiCard';
import UploadForms from './UploadForms';

const Dashboard = () => {
  const [summaryData, setSummaryData] = useState<DashboardSummary | null>(null); // Usa o tipo importado
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const data: DashboardSummary = await api.getDashboardSummary(); // Garante que os dados sigam o tipo
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
  }, [fetchData]);

  const renderContent = () => {
    if (loading) {
      return <div className="text-center p-10">Carregando dados do dashboard...</div>;
    }

    if (error) {
      return <div className="text-center p-10 text-red-400">{error}</div>;
    }

    if (!summaryData) {
      return <div className="text-center p-10">Nenhum dado para exibir. Faça um upload para começar.</div>;
    }

    const { kpi_summary, last_action_plan, trend_history } = summaryData;

    if (!kpi_summary) {
      return <div className="text-center p-10">Dados de KPI não disponíveis. Faça um upload para gerar um relatório.</div>;
    }

    const getSuccessClasses = (rate: number) => {
      if (rate < 50) return { color: 'text-danger', border: 'card-neon-red' } as const;
      if (rate < 70) return { color: 'text-warning', border: 'card-neon-warning' } as const;
      return { color: 'text-success', border: 'card-neon-green' } as const;
    };

    const successClasses = getSuccessClasses(kpi_summary.taxa_sucesso_valor);

    return (
      <div className="kpi-dashboard">
        <KpiCard
          title="Casos sem Remediação"
          value={kpi_summary.casos_atuacao}
          subValue={kpi_summary.alertas_atuacao}
          subLabel="Alertas"
          colorClass={kpi_summary.casos_atuacao > 0 ? 'text-danger' : 'text-success'}
          borderClass={kpi_summary.casos_atuacao > 0 ? 'card-neon-red' : 'card-neon-green'}
        />
        <KpiCard
          title="Casos com Instabilidade"
          value={kpi_summary.casos_instabilidade}
          subValue={kpi_summary.alertas_instabilidade}
          subLabel="Alertas"
          colorClass={kpi_summary.casos_instabilidade > 0 ? 'text-warning' : 'text-success'}
          borderClass={kpi_summary.casos_instabilidade > 0 ? 'card-neon-warning' : 'card-neon-green'}
        />
        <KpiCard
          title="Sucesso da Automação"
          value={kpi_summary.taxa_sucesso_automacao}
          subValue={`${kpi_summary.casos_sucesso} de ${kpi_summary.total_casos} Casos`}
          colorClass={successClasses.color}
          borderClass={successClasses.border}
        />
      </div>
    );
  };

  return (
    <>
      {/* O card de KPIs só será renderizado se houver dados de KPI */}
      {summaryData && summaryData.kpi_summary && (
        <div className="card">
          <header className="mb-8 flex items-center gap-4 justify-center">
            <LayoutDashboard className="w-8 h-8 text-blue-400" />
            <h1 className="text-3xl font-bold text-white">Dashboard de Análise</h1>
          </header>
          {renderContent()}
        </div>
      )}
      <UploadForms onUploadSuccess={fetchData} />
    </>
  );
};

export default Dashboard;