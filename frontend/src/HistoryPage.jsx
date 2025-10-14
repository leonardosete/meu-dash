import { useState, useEffect } from 'react';
import { fetchAllReports, deleteReport } from '../services/api';
import Spinner from '../components/Spinner';

function HistoryPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      setLoading(true);
      const data = await fetchAllReports();
      setReports(data.reports);
    } catch (err) {
      setError(err.message || 'Erro ao carregar histórico.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (reportId) => {
    // Placeholder for authentication token
    const adminToken = 'seu-token-secreto-aqui'; // TODO: Substituir pelo token real do estado de autenticação

    if (window.confirm(`Tem certeza que deseja deletar o relatório ID ${reportId}?`)) {
      try {
        await deleteReport(reportId, adminToken);
        // Recarrega a lista de relatórios após a exclusão
        setReports(reports.filter(report => report.id !== reportId));
      } catch (err) {
        alert(`Falha ao deletar: ${err.message}`);
      }
    }
  };

  if (loading) return <Spinner />;
  if (error) return <div role="alert">Erro: {error}</div>;

  return (
    <div className="history-page">
      <h1>Histórico de Relatórios</h1>
      <table className="history-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Data de Criação</th>
            <th>Relatório</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {reports.length > 0 ? (
            reports.map(report => (
              <tr key={report.id}>
                <td>{report.id}</td>
                <td>{new Date(report.created_at).toLocaleString('pt-BR')}</td>
                <td>
                  <a href={report.report_url} target="_blank" rel="noopener noreferrer">
                    Ver Relatório
                  </a>
                </td>
                <td><button onClick={() => handleDelete(report.id)} className="delete-button">Deletar</button></td>
              </tr>
            ))
          ) : (
            <tr><td colSpan="4">Nenhum relatório encontrado.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default HistoryPage;