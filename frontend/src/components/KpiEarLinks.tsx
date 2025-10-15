import React from 'react';

// Define as propriedades que o componente receberá
interface KpiEarLinksProps {
  reportUrl?: string;
  actionPlanUrl?: string;
  trendAnalysisUrl?: string;
}

const KpiEarLinks: React.FC<KpiEarLinksProps> = ({ reportUrl, actionPlanUrl, trendAnalysisUrl }) => {
  // Se nenhuma URL for fornecida, o componente não renderiza nada.
  if (!reportUrl && !actionPlanUrl && !trendAnalysisUrl) {
    return null;
  }
    
  return (
    <div className="kpi-ear-links">
      {/* Link para o Relatório Completo */}
      {reportUrl && (
        <a 
          href={reportUrl} 
          className="report-link-ear visible has-tooltip" 
          data-tooltip="Acessar Relatório Completo" 
          style={{ backgroundColor: 'var(--accent-color)' }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
            <polyline points="15 3 21 3 21 9"></polyline>
            <line x1="10" y1="14" x2="21" y2="3"></line>
          </svg>
        </a>
      )}

      {/* Link para o Plano de Ação */}
      {actionPlanUrl && (
        <a 
          href={actionPlanUrl} 
          className="report-link-ear visible has-tooltip" 
          data-tooltip="Ver Plano de Ação" 
          style={{ backgroundColor: 'var(--danger-color)' }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <circle cx="12" cy="12" r="6"></circle>
            <circle cx="12" cy="12" r="2"></circle>
          </svg>
        </a>
      )}

      {/* Link para a Análise de Tendência */}
      {trendAnalysisUrl && (
        <a 
          href={trendAnalysisUrl} 
          className="report-link-ear visible has-tooltip" 
          data-tooltip="Ver Análise de Tendência" 
          style={{ backgroundColor: 'var(--success-color)' }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
        </a>
      )}
    </div>
  );
};

export default KpiEarLinks;