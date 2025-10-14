import { useState, useEffect } from 'react';
import { fetchDashboardSummary } from '../services/api';
import KpiCard from './KpiCard';
import LastActionPlan from './components/LastActionPlan';
import Spinner from './Spinner';
import TrendHistory from './components/TrendHistory';
import UploadForm from './components/UploadForm';

function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const summaryData = await fetchDashboardSummary();
      setData(summaryData);
    } catch (err) {
      setError(err.message || 'Ocorreu um erro desconhecido.');
    } finally {
      setLoading(false);
    }
  };

  // Esta função será chamada pelo UploadForm para recarregar os dados.
  const handleUploadSuccess = () => loadData();

  if (loading) {
    return <Spinner />;
  }

  if (error) {
    return <div role="alert">Erro ao buscar dados: {error}</div>;
  }

  if (!data || !data.kpi_summary) {
    return <p>Nenhum dado de KPI disponível. Faça um upload para começar.</p>;
  }

  const { kpi_summary, trend_history, last_action_plan } = data;

  return (
    <div className="dashboard">
      <h1>Dashboard de Análise de Alertas</h1>
      <UploadForm onUploadSuccess={handleUploadSuccess} />
      <section className="kpi-container" aria-labelledby="kpi-heading">
        <h2 id="kpi-heading" className="sr-only">Resumo de KPIs</h2>
        <KpiCard title="Total de Casos Analisados" value={kpi_summary.total_casos} />
        <KpiCard title="Casos para Atuação" value={kpi_summary.casos_atuacao} />
        <KpiCard title="Casos de Instabilidade" value={kpi_summary.casos_instabilidade} />
        <KpiCard title="Sucesso da Automação" value={kpi_summary.taxa_sucesso_automacao} />
      </section>
      <div className="dashboard-columns">
        <TrendHistory history={trend_history} />
        <LastActionPlan actionPlan={last_action_plan} />
      </div>
    </div>
  );
}

export default Dashboard;