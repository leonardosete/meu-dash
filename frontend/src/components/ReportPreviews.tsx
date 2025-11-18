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
  return (
    <div className="report-previews-container page-fade-in">
      <div className="previews-header">
        <div>
          <h2>Análise Concluída</h2>
          {dateRange && (
            <p className="previews-date-range">Período: {dateRange}</p>
          )}
        </div>
      </div>

      {/* Bloco movido para cima, conforme solicitado */}
      {quickDiagnosis && (
        <div className="quick-diagnosis-wrapper">
          <div
            className="card highlight"
            dangerouslySetInnerHTML={{ __html: quickDiagnosis }}
          />
        </div>
      )}

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
                <ExternalLink size={18} />
              </a>
            </div>
            {/* Iframe Wrapper */}
            <div className="iframe-wrapper">
              <iframe src={urls.summary} title="Relatório Completo" />
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
                <ExternalLink size={18} />
              </a>
            </div>
            {/* Iframe Wrapper */}
            <div className="iframe-wrapper">
              <iframe src={urls.action_plan} title="Plano de Ação" />
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
                <ExternalLink size={18} />
              </a>
            </div>
            {/* Iframe Wrapper */}
            <div className="iframe-wrapper">
              <iframe src={urls.trend} title="Análise Comparativa" />
            </div>
          </div>
        )}
      </div>

      {/* O bloco quickDiagnosis foi movido daqui para cima */}
    </div>
  );
};

export default ReportPreviews;