import React from 'react';
import { ReportUrls } from '../types';
import { ExternalLink } from 'lucide-react';

interface ReportPreviewsProps {
  urls: ReportUrls;
}

const ReportPreviews: React.FC<ReportPreviewsProps> = ({ urls }) => {
  return (
    <div className="report-previews-container">
      <div className="previews-header">
        <h2>Relatórios Gerados</h2>
      </div>
      <div className="previews-grid">
        {urls.summary && (
          <div className="preview-card">
            <div className="preview-card-header">
              <h3>Resumo Geral</h3>
              <a href={urls.summary} target="_blank" rel="noopener noreferrer" className="preview-external-link" title="Abrir em nova aba">
                <ExternalLink size={20} />
              </a>
            </div>
            <div className="iframe-wrapper">
              <iframe src={urls.summary} title="Resumo Geral" loading="lazy"></iframe>
            </div>
          </div>
        )}
        {urls.action_plan && (
          <div className="preview-card">
            <div className="preview-card-header">
              <h3>Plano de Ação</h3>
              <a href={urls.action_plan} target="_blank" rel="noopener noreferrer" className="preview-external-link" title="Abrir em nova aba">
                <ExternalLink size={20} />
              </a>
            </div>
            <div className="iframe-wrapper">
              <iframe src={urls.action_plan} title="Plano de Ação" loading="lazy"></iframe>
            </div>
          </div>
        )}
        {urls.trend && (
          <div className="preview-card">
            <div className="preview-card-header">
              <h3>Análise de Tendência</h3>
              <a href={urls.trend} target="_blank" rel="noopener noreferrer" className="preview-external-link" title="Abrir em nova aba">
                <ExternalLink size={20} />
              </a>
            </div>
            <div className="iframe-wrapper">
              <iframe src={urls.trend} title="Análise de Tendência" loading="lazy"></iframe>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportPreviews;