import React, { useState, useEffect } from 'react';
import * as api from '../services/api';
import { useAuth } from '../hooks/useAuth';

// Define a interface para o tipo de dado de um relatório
interface Report {
  id: number;
  timestamp: string;
  original_filename: string;
  date_range: string;
  url: string;
}

const HistoryPage: React.FC = () => {
  const [reports, setReports] = useState<Report[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    const fetchReports = async () => {
      try {
        setIsLoading(true);
        const data = await api.getReports();
        setReports(data);
      } catch (err: any) {
        setError(err.message || 'Falha ao buscar o histórico de relatórios.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchReports();
  }, []); // O array vazio garante que o efeito rode apenas uma vez, ao montar o componente.

  const handleDelete = async (reportId: number) => {
    if (window.confirm('Tem certeza que deseja excluir este relatório? Esta ação não pode ser desfeita.')) {
      try {
        await api.deleteReport(reportId);
        // Atualiza a lista de relatórios no estado, removendo o que foi excluído.
        setReports(reports.filter(report => report.id !== reportId));
      } catch (err: any) {
        // Exibe o erro para o usuário, caso a exclusão falhe (ex: token expirado)
        setError(err.response?.data?.error || 'Falha ao excluir o relatório.');
        // Remove a mensagem de erro após alguns segundos
        setTimeout(() => setError(null), 5000);
      }
    }
  };

  if (isLoading) {
    return <div className="card"><h2>Carregando Histórico...</h2></div>;
  }

  if (error) {
    return <div className="card error-message"><h2>Erro</h2><p>{error}</p></div>;
  }

  return (
    <div className="card">
      <h2>Histórico de Análises</h2>
      {error && <div className="error-message mb-4">{error}</div>}
      {reports.length === 0 ? (
        <p>Nenhum relatório encontrado no histórico.</p>
      ) : (
        <table className="history-table">
          <thead>
            <tr>
              <th>Data da Análise</th>
              <th>Arquivo Original</th>
              <th>Período Analisado</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.id}>
                <td>{new Date(report.timestamp).toLocaleString('pt-BR')}</td>
                <td>{report.original_filename}</td>
                <td>{report.date_range || 'N/A'}</td>
                <td className="actions-cell">
                  <a href={`${api.API_BASE_URL}${report.url}`} target="_blank" rel="noopener noreferrer" className="action-button view">Visualizar</a>
                  <button onClick={() => handleDelete(report.id)} className="action-button delete" disabled={!isAuthenticated}>Excluir</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default HistoryPage;