import React from "react";
import { ReportUrls } from "../types";
import { ExternalLink, FileText, BarChart3, TrendingUp } from "lucide-react";

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
            <div className="preview-card-body">
              <FileText size={64} strokeWidth={1} />
              <a
                href={urls.summary}
                target="_blank"
                rel="noopener noreferrer"
                className="preview-button"
              >
                Abrir Relatório
              </a>
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
            <div className="preview-card-body">
              <BarChart3 size={64} strokeWidth={1} />
              <a
                href={urls.action_plan}
                target="_blank"
                rel="noopener noreferrer"
                className="preview-button"
              >
                Abrir Plano de Ação
              </a>
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
            <div className="preview-card-body">
              <TrendingUp size={64} strokeWidth={1} />
              <a
                href={urls.trend}
                target="_blank"
                rel="noopener noreferrer"
                className="preview-button"
              >
                Abrir Análise
              </a>
            </div>
          </div>
        )}
      </div>

      {quickDiagnosis && (
        <div className="quick-diagnosis-wrapper">
          <div
            className="card highlight"
            dangerouslySetInnerHTML={{ __html: quickDiagnosis }}
          />
        </div>
      )}
    </div>
  );
};

export default ReportPreviews;