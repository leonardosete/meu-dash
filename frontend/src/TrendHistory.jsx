/* eslint-disable react/prop-types */
function TrendHistory({ history }) {
  return (
    <section className="trend-history-section">
      <h2>Histórico de Análises de Tendência</h2>
      {history && history.length > 0 ? (
        <ul>
          {history.map((item) => (
            <li key={item.id}>
              <a href={item.report_url} target="_blank" rel="noopener noreferrer">
                Análise de {new Date(item.created_at).toLocaleDateString('pt-BR')}
              </a>
            </li>
          ))}
        </ul>
      ) : (
        <p>Nenhum histórico de análise de tendência encontrado.</p>
      )}
    </section>
  );
}

export default TrendHistory;