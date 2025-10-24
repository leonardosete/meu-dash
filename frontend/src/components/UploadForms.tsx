import React, { useState } from 'react';
import FileInput from './FileInput';
import { uploadStandardAnalysis, uploadComparativeAnalysis, login as apiLogin } from '../services/api';
import { Loader2, Lock, LogOut } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

interface UploadFormsProps {
  onUploadSuccess: () => void;
}

const UploadForms: React.FC<UploadFormsProps> = ({ onUploadSuccess }) => {
  const { isAuthenticated, login, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<'padrao' | 'comparativa'>('padrao');
  const [padraoFile, setPadraoFile] = useState<FileList | null>(null);
  const [fileAntigo, setFileAntigo] = useState<FileList | null>(null);
  const [fileRecente, setFileRecente] = useState<FileList | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [standardError, setStandardError] = useState<string | null>(null);
  const [comparativeError, setComparativeError] = useState<string | null>(null);

  // Estado para o formulário de login inline
  const [isLoginVisible, setIsLoginVisible] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState<string | null>(null);
  const [isLoginLoading, setIsLoginLoading] = useState(false);

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
      onUploadSuccess();
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
      const result = await uploadComparativeAnalysis(fileAntigo[0], fileRecente[0]);
      if (result.report_url) {
        window.location.href = result.report_url;
      }
    } catch (err: any) {
      setComparativeError(err.response?.data?.error || 'Ocorreu um erro na comparação.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsLoginLoading(true);
    setLoginError(null);
    try {
      const { access_token } = await apiLogin({ username, password });
      login(access_token);
      setIsLoginVisible(false);
    } catch (err: any) {
      setLoginError(err.response?.data?.error || 'Falha na autenticação.');
    } finally {
      setIsLoginLoading(false);
    }
  };

  const renderOverlayContent = () => {
    if (!isLoginVisible) {
      return (
        <button type="button" className="overlay-content" onClick={() => setIsLoginVisible(true)}>
          <Lock size={24} />
          <span>Faça login para habilitar o upload de arquivos.</span>
        </button>
      );
    }

    return (
      <div className="inline-login-form-container" onClick={(e) => e.stopPropagation()}>
        <h3>Acesso Administrativo</h3>
        {loginError && <div className="error-message small">{loginError}</div>}
        <form onSubmit={handleLoginSubmit} className="inline-login-form">
          <div className="input-group">
            <label htmlFor="inline-username">Usuário</label>
            <input
              id="inline-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="input-group">
            <label htmlFor="inline-password">Senha</label>
            <input
              id="inline-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" disabled={isLoginLoading}>
            {isLoginLoading ? <Loader2 className="animate-spin" /> : 'Entrar'}
          </button>
        </form>
      </div>
    );
  };

  return (
    <div className="form-section">
      <div className="tab-container" style={{ position: 'relative' }}>
        {isAuthenticated && (
          <button 
            onClick={logout} 
            className="logout-ear-button"
            title="Sair do Modo Admin"
          >
            <LogOut size={20} />
          </button>
        )}
        {!isAuthenticated && (
          <div className="form-disabled-overlay">
            {renderOverlayContent()}
          </div>
        )}
        <div className={!isAuthenticated ? 'forms-wrapper-disabled' : ''}>
          <div className="tab-links">
            <button className={`tab-link ${activeTab === 'padrao' ? 'active' : ''}`} onClick={() => setActiveTab('padrao')}>Análise Padrão</button>
            <button className={`tab-link ${activeTab === 'comparativa' ? 'active' : ''}`} onClick={() => setActiveTab('comparativa')}>Análise Comparativa</button>
          </div>
          <div id="tab-padrao" className={`tab-content ${activeTab === 'padrao' ? 'active' : ''}`}>
            {standardError && <div className="error-message">{standardError}</div>}
            <p className="tab-description">Processe o arquivo de dados mais recente. O sistema o comparará com a última análise registrada no histórico para gerar um relatório completo e a análise de tendência contínua.</p>
            <form onSubmit={handlePadraoSubmit}>
              <label htmlFor="file_recente" className="form-label">Selecione o arquivo de dados mais recente:</label>
              <FileInput id="file_recente" name="file_recente" onFileChange={setPadraoFile} isMultiple={false} />
              <button type="submit" disabled={isLoading}>
                {isLoading ? <Loader2 className="animate-spin" /> : 'Analisar e Comparar com Histórico'}
              </button>
            </form>
          </div>
          <div id="tab-comparativa" className={`tab-content ${activeTab === 'comparativa' ? 'active' : ''}`}>
            {comparativeError && <div className="error-message">{comparativeError}</div>}
            <p className="tab-description">Compare dois arquivos de dados específicos para gerar um relatório de tendência sob demanda. Ideal para análises pontuais e investigativas entre períodos não sequenciais.</p>
            <form onSubmit={handleComparativaSubmit}>
              <label htmlFor="file_antigo" className="form-label">Selecione o arquivo de dados mais antigo (base):</label>
              <FileInput id="file_antigo" name="file_antigo" onFileChange={setFileAntigo} isMultiple={false} />
              <label htmlFor="file_recente_comp" className="form-label" style={{ marginTop: '15px' }}>Selecione o arquivo de dados mais recente:</label>
              <FileInput id="file_recente_comp" name="file_recente_comp" onFileChange={setFileRecente} isMultiple={false} />
              <button type="submit" disabled={isLoading}>
                {isLoading ? <Loader2 className="animate-spin" /> : 'Comparar Arquivos'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadForms;