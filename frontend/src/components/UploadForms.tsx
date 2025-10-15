import React, { useState } from 'react';
import FileInput from './FileInput';
import * as api from '../services/api';

interface UploadFormsProps {
  onUploadSuccess: () => void;
}

const UploadForms: React.FC<UploadFormsProps> = ({ onUploadSuccess }) => {
  const [activeTab, setActiveTab] = useState<'padrao' | 'comparativa'>('padrao');
  const [padraoFile, setPadraoFile] = useState<FileList | null>(null);
  const [comparativaFiles, setComparativaFiles] = useState<FileList | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePadraoSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!padraoFile || padraoFile.length === 0) {
      alert('Por favor, selecione um arquivo.');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      await api.uploadStandardAnalysis(padraoFile[0]);
      onUploadSuccess(); // Recarrega o dashboard
    } catch (err: any) {
      setError(err.response?.data?.error || 'Ocorreu um erro no upload.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleComparativaSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!comparativaFiles || comparativaFiles.length !== 2) {
      alert('Por favor, selecione exatamente dois arquivos.');
      return;
    }
    // TODO: Implementar lógica de chamada da API para análise comparativa
    console.log('Análise Comparativa com:', comparativaFiles);
  };

  return (
    <div className="card form-card">
      {error && <div className="error-message">{error}</div>}
      <div className="tab-container">
        <div className="tab-links">
          <button className={`tab-link ${activeTab === 'padrao' ? 'active' : ''}`} onClick={() => setActiveTab('padrao')}>Análise Padrão</button>
          <button className={`tab-link ${activeTab === 'comparativa' ? 'active' : ''}`} onClick={() => setActiveTab('comparativa')}>Análise Comparativa</button>
        </div>

        <div id="tab-padrao" className={`tab-content ${activeTab === 'padrao' ? 'active' : ''}`}>
          <p className="tab-description">Processe o arquivo de dados mais recente. O sistema o comparará com a última análise registrada no histórico para gerar um relatório completo e a análise de tendência contínua.</p>
          <form onSubmit={handlePadraoSubmit}>
            <label htmlFor="file_recente">Selecione o arquivo de dados mais recente:</label>
            <FileInput id="file_recente" name="file_recente" onFileChange={setPadraoFile} />
            <button type="submit" disabled={isLoading}>
              {isLoading ? 'Analisando...' : 'Analisar e Comparar com Histórico'}
            </button>
          </form>
        </div>

        <div id="tab-comparativa" className={`tab-content ${activeTab === 'comparativa' ? 'active' : ''}`}>
          <p className="tab-description">Compare dois arquivos de dados específicos para gerar um relatório de tendência sob demanda. Ideal para análises pontuais e investigativas entre períodos não sequenciais.</p>
          <form onSubmit={handleComparativaSubmit}>
            <label htmlFor="file_comparativa">Selecione exatamente dois arquivos para comparar:</label>
            <FileInput id="file_comparativa" name="files" isMultiple={true} onFileChange={setComparativaFiles} />
            <button type="submit">Comparar Arquivos</button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default UploadForms;