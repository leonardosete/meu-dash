import React, { useState, useEffect } from "react";
import * as api from "../services/api";
import "./HistoryPage.css"; // Importa o CSS específico
import { useAuth } from "../hooks/useAuth";
import { Report } from "../types"; // Importa o tipo Report atualizado

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
        setError(err.message || "Falha ao buscar o histórico de relatórios.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchReports();
  }, []);

  const handleDelete = async (reportId: string) => {
    if (
      window.confirm(
        "Tem certeza que deseja excluir este relatório? Esta ação não pode ser desfeita.",
      )
    ) {
      try {
        // Extrai o ID numérico do formato 'type-id'
        const numericId = parseInt(reportId.split("-")[1], 10);
        if (isNaN(numericId)) {
          throw new Error("ID de relatório inválido.");
        }

        await api.deleteReport(numericId);
        setReports(reports.filter((report) => report.id !== reportId));
      } catch (err: any) {
        setError(err.response?.data?.error || "Falha ao excluir o relatório.");
        setTimeout(() => setError(null), 5000);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="card">
        <h2>Carregando Histórico...</h2>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card error-message">
        <h2>Erro</h2>
        <p>{error}</p>
      </div>
    );
  }

  const standardReports = reports.filter(
    (report) => report.type === "standard",
  );
  const comparativeReports = reports.filter(
    (report) => report.type === "comparative",
  );

  return (
    <div className="history-page-container">
      <h2>Histórico de Análises</h2>
      {error && <div className="error-message mb-4">{error}</div>}

      {reports.length === 0 ? (
        <div className="card">
          <p>Nenhum relatório encontrado no histórico.</p>
        </div>
      ) : (
        <>
          <div className="card history-card">
            <h3>Análises Padrão</h3>
            {standardReports.length > 0 ? (
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
                  {standardReports.map((report) => (
                    <tr key={report.id} className="report-row">
                      <td>
                        {new Date(report.timestamp).toLocaleString("pt-BR")}
                      </td>
                      <td>{report.original_filename}</td>
                      <td>{report.date_range || "N/A"}</td>
                      <td>
                        <div className="action-buttons-container">
                          <a
                            href={`${api.API_BASE_URL}${report.url}`}
                            className="action-button view"
                          >
                            Visualizar
                          </a>
                          {isAuthenticated && (
                            <button
                              onClick={() => handleDelete(report.id)}
                              className="action-button delete"
                            >
                              Excluir
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p>Nenhuma análise padrão encontrada.</p>
            )}
          </div>

          <div className="card history-card">
            <h3>Análises Comparativas</h3>
            {comparativeReports.length > 0 ? (
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Data da Análise</th>
                    <th>Comparação</th>
                    <th>Período Analisado</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {comparativeReports.map((report) => (
                    <tr key={report.id} className="report-row">
                      <td>
                        {new Date(report.timestamp).toLocaleString("pt-BR")}
                      </td>
                      <td>{report.original_filename}</td>
                      <td>{report.date_range || "N/A"}</td>
                      <td>
                        <div className="action-buttons-container">
                          <a
                            href={`${api.API_BASE_URL}${report.url}`}
                            className="action-button view"
                          >
                            Visualizar
                          </a>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p>Nenhuma análise comparativa encontrada.</p>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default HistoryPage;
