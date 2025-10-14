import { useState, useEffect } from 'react';
import './App.css';

// Define a interface para os dados dos KPIs para garantir a tipagem
interface KpiSummary {
  total_casos: number;
  casos_atuacao: number;
  casos_instabilidade: number;
  taxa_sucesso_automacao: string;
}

function App() {
  // Estados para armazenar os dados da API e o status de carregamento/erro
  const [kpiSummary, setKpiSummary] = useState<KpiSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // useEffect para buscar os dados da API quando o componente é montado
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // A chamada é feita para /api/... e o proxy do Vite irá redirecionar
        // para http://backend:5000/api/...
        const response = await fetch('/api/v1/dashboard-summary');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setKpiSummary(data.kpi_summary);
      } catch (e) {
        if (e instanceof Error) {
          setError(e.message);
        } else {
          setError('An unknown error occurred');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []); // O array vazio [] garante que o efeito rode apenas uma vez

  if (loading) return <div>Carregando dados do dashboard...</div>;
  if (error) return <div>Erro ao buscar dados: {error}</div>;

  return (
    <div className="dashboard">
      <h1>Dashboard de Análise de Alertas</h1>
      <div className="kpi-container">
        {kpiSummary ? (
          <>
            <div className="kpi-card">
              <h3>Casos para Atuação</h3>
              <p className="value">{kpiSummary.casos_atuacao}</p>
            </div>
            {/* Adicione outros cards de KPI aqui */}
          </>
        ) : (
          <p>Nenhum dado de KPI disponível. Faça um upload para começar.</p>
        )}
      </div>
    </div>
  );
}

export default App;