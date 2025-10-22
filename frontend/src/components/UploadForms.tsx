import React, { useState } from 'react';
import FileInput from './FileInput';
import { uploadStandardAnalysis, uploadComparativeAnalysis } from '../services/api';
import { Loader2 } from 'lucide-react'; // Ícone de spinner

interface UploadFormsProps {
  onUploadSuccess: () => void;
}

const UploadForms: React.FC<UploadFormsProps> = ({ onUploadSuccess }) => {
  const [activeTab, setActiveTab] = useState<'padrao' | 'comparativa'>('padrao');
  const [padraoFile, setPadraoFile] = useState<FileList | null>(null);
  const [fileAntigo, setFileAntigo] = useState<FileList | null>(null);
  const [fileRecente, setFileRecente] = useState<FileList | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [standardError, setStandardError] = useState<string | null>(null);
  const [comparativeError, setComparativeError] = useState<string | null>(null);

  const handlePadraoSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!padraoFile || padraoFile.length === 0) {
      alert('Por favor, selecione um arquivo.');
      return;
    }
    setIsLoading(true);
    setStandardError(null);
    try {
      await uploadStandardAnalysis(padraoFile[0]);
      onUploadSuccess(); // Recarrega o dashboard
    } catch (err: any) {
      setStandardError(err.response?.data?.error || 'Ocorreu um erro no upload.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleComparativaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileAntigo || fileAntigo.length === 0) {
      setComparativeError('Por favor, selecione o arquivo antigo.');
      return;
    }
    if (!fileRecente || fileRecente.length === 0) {
      setComparativeError('Por favor, selecione o arquivo recente.');
      return;
    }
    setIsLoading(true);
    setComparativeError(null);
    try {
      // Passa os arquivos separadamente para o serviço
      const result = await uploadComparativeAnalysis(fileAntigo[0], fileRecente[0]);
      if (result.report_url) {
        // Navega para o relatório gerado na mesma aba
        window.location.href = result.report_url;
      }
    } catch (err: any) {
      setComparativeError(err.response?.data?.error || 'Ocorreu um erro na comparação.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card form-card">
      <div className="tab-container">
        <div className="tab-links">
          <button className={`tab-link ${activeTab === 'padrao' ? 'active' : ''}`} onClick={() => setActiveTab('padrao')}>Análise Padrão</button>
          <button className={`tab-link ${activeTab === 'comparativa' ? 'active' : ''}`} onClick={() => setActiveTab('comparativa')}>Análise Comparativa</button>
        </div>

        <div id="tab-padrao" className={`tab-content ${activeTab === 'padrao' ? 'active' : ''}`}>
          {standardError && <div className="error-message">{standardError}</div>}
          <p className="tab-description">Processe o arquivo de dados mais recente. O sistema o comparará com a última análise registrada no histórico para gerar um relatório completo e a análise de tendência contínua.</p>
          <form onSubmit={handlePadraoSubmit}>
            <label htmlFor="file_recente">Selecione o arquivo de dados mais recente:</label>
            <FileInput id="file_recente" name="file_recente" onFileChange={setPadraoFile} isMultiple={false} />
            <button type="submit" disabled={isLoading}>
              {isLoading ? (
                <Loader2 className="animate-spin" />
              ) : (
                'Analisar e Comparar com Histórico'
              )}
            </button>
          </form>
        </div>

        <div id="tab-comparativa" className={`tab-content ${activeTab === 'comparativa' ? 'active' : ''}`}>
          {comparativeError && <div className="error-message">{comparativeError}</div>}
          <p className="tab-description">Compare dois arquivos de dados específicos para gerar um relatório de tendência sob demanda. Ideal para análises pontuais e investigativas entre períodos não sequenciais.</p>
          <form onSubmit={handleComparativaSubmit}>
            <label htmlFor="file_antigo">Selecione o arquivo de dados mais antigo (base):</label>
            <FileInput id="file_antigo" name="file_antigo" onFileChange={setFileAntigo} isMultiple={false} />

            <label htmlFor="file_recente_comp" style={{ marginTop: '15px' }}>Selecione o arquivo de dados mais recente:</label>
            <FileInput id="file_recente_comp" name="file_recente" onFileChange={setFileRecente} isMultiple={false} />

            <button type="submit" disabled={isLoading}>
              {isLoading ? (
                <Loader2 className="animate-spin" />
              ) : (
                'Comparar Arquivos'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default UploadForms;