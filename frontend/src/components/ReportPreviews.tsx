import React from 'react';
import { ReportUrls } from '../types';

interface ReportPreviewsProps {
  urls: ReportUrls;
}

const ReportPreviews: React.FC<ReportPreviewsProps> = ({ urls }) => {
  return (
    <div className="report-previews-container">
      <div className="previews-header">
        <h2>Relatórios Gerados</h2>
      </div>
      <p className="previews-description">
        A análise foi concluída. Abaixo estão os principais relatórios gerados.
      </p>
      <div className="previews-grid">
        {urls.summary && (
          <div className="preview-card">
            <h3>Resumo Geral</h3>
            <div className="iframe-wrapper">
              <iframe src={urls.summary} title="Resumo Geral" loading="lazy"></iframe>
            </div>
            <a href={urls.summary} target="_blank" rel="noopener noreferrer" className="preview-link">
              Abrir em nova aba
            </a>
          </div>
        )}
        {urls.action_plan && (
          <div className="preview-card">
            <h3>Plano de Ação</h3>
            <div className="iframe-wrapper">
              <iframe src={urls.action_plan} title="Plano de Ação" loading="lazy"></iframe>
            </div>
            <a href={urls.action_plan} target="_blank" rel="noopener noreferrer" className="preview-link">
              Abrir em nova aba
            </a>
          </div>
        )}
        {urls.trend && (
          <div className="preview-card">
            <h3>Análise de Tendência</h3>
            <div className="iframe-wrapper">
              <iframe src={urls.trend} title="Análise de Tendência" loading="lazy"></iframe>
            </div>
            <a href={urls.trend} target="_blank" rel="noopener noreferrer" className="preview-link">
              Abrir em nova aba
            </a>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportPreviews;