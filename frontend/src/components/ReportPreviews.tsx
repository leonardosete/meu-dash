// ... (imports e definição do componente)

const ReportPreviews: React.FC<ReportPreviewsProps> = ({
  urls,
  quickDiagnosis,
  dateRange,
}) => {
  // ... (cabeçalho)

  return (
    <div className="report-previews-container">
      {/* ... */}
      <div className="previews-grid">
        {urls.summary && (
          <div className="preview-card">
            {/* ... */}
            <div className="iframe-wrapper">
              <iframe
                src={urls.summary}
                title="Relatório Completo"
                loading="lazy"
              ></iframe>
            </div>
          </div>
        )}
        {urls.action_plan && (
          <div className="preview-card">
            {/* ... */}
            <div className="iframe-wrapper">
              <iframe
                src={urls.action_plan}
                title="Plano de Ação"
                loading="lazy"
              ></iframe>
            </div>
          </div>
        )}
        {urls.trend && (
          <div className="preview-card">
            {/* ... */}
            <div className="iframe-wrapper">
              <iframe
                src={urls.trend}
                title="Análise Comparativa"
                loading="lazy"
              ></iframe>
            </div>
          </div>
        )}
      </div>
      {/* ... (diagnóstico rápido) */}
    </div>
  );
};

export default ReportPreviews;