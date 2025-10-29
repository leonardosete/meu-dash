import React from "react";
import { ReportUrls } from "../types";
import { ExternalLink } from "lucide-react";

interface ReportPreviewsProps {
  urls: ReportUrls;
  quickDiagnosis: string | null;
  dateRange: string | null;
}

const ReportPreviews: React.FC<ReportPreviewsProps> = ({
  urls,
  quickDiagnosis,
  dateRange,
}) => {
  const hasAllThree = urls.summary && urls.action_plan && urls.trend;

  return (
    <div className="report-previews-container">
      <div className="previews-header">
        <h2>Relatórios Gerados</h2>
        {dateRange && (
          <span className="previews-date-range">({dateRange})</span>
        )}
      </div>
      <div className="previews-grid">
        {urls.summary && (
          <div className="preview-card">
            <div className="preview-card-header">
              <h3>Relatório Completo</h3>
              <a
                href={urls.summary}
                target="_blank"
                rel="noopener noreferrer"
                className="preview-external-link"
                title="Abrir em nova aba"
              >
                <ExternalLink size={20} />
              </a>
            </div>
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
            <div className="preview-card-header">
              <h3>Plano de Ação</h3>
              <a
                href={urls.action_plan}
                target="_blank"
                rel="noopener noreferrer"
                className="preview-external-link"
                title="Abrir em nova aba"
              >
                <ExternalLink size={20} />
              </a>
            </div>
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
            <div className="preview-card-header">
              <h3>Análise Comparativa</h3>
              <a
                href={urls.trend}
                target="_blank"
                rel="noopener noreferrer"
                className="preview-external-link"
                title="Abrir em nova aba"
              >
                <ExternalLink size={20} />
              </a>
            </div>
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
      {hasAllThree && quickDiagnosis && (
        <div
          className="quick-diagnosis-wrapper"
          dangerouslySetInnerHTML={{ __html: quickDiagnosis }}
        />
      )}
    </div>
  );
};

export default ReportPreviews;
