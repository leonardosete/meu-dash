import axios from 'axios';
import { DashboardSummary, LoginCredentials, Report, UploadSuccessResponse } from '../types';

// Em produção (import.meta.env.PROD é true), a URL base é uma string vazia,
// tornando as chamadas de API relativas ao domínio atual (ex: /api/v1/...).
// Em desenvolvimento, ele usa a variável de ambiente ou o fallback para o servidor local.
export const API_BASE_URL = import.meta.env.PROD
  ? ''
  : (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001');

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Permite o envio de cookies, se necessário para autenticação
});

// Interceptor para adicionar o token de autenticação a cada requisição, se ele existir.
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('meu_dash_auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  // Lançar o erro é a forma moderna de propagá-lo na cadeia de promessas.
  throw error;
});

// Interceptor para tratar erros de resposta globalmente.
// Isso é útil para lidar com casos como tokens expirados.
apiClient.interceptors.response.use(
  (response) => response, // Se a resposta for bem-sucedida, apenas a repassa.
  (error) => {
    // Se o erro for 401 (Não Autorizado), significa que o token é inválido ou expirou.
    if (error.response && error.response.status === 401) {
      // Remove o token inválido do armazenamento local.
      localStorage.removeItem('meu_dash_auth_token');
      // Recarrega a aplicação para redefinir o estado de autenticação, usando 'globalThis' para portabilidade.
      globalThis.location.reload();
    }
    // Propaga o erro para que possa ser tratado pelo código que fez a chamada.
    throw error;
  }
);


/**
 * Busca os dados de resumo para o dashboard principal.
 */
export const getDashboardSummary = async (): Promise<DashboardSummary> => {
  const response = await apiClient.get('/api/v1/dashboard-summary');
  return response.data;
};

/**
 * Envia um arquivo para a análise padrão.
 * @param file O arquivo a ser enviado.
 */
export const uploadStandardAnalysis = async (file: File): Promise<UploadSuccessResponse> => {
  const formData = new FormData();
  formData.append('file_recente', file);

  const response = await apiClient.post('/api/v1/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * Busca a lista de todos os relatórios gerados.
 */
export const getReports = async (): Promise<Report[]> => {
  const response = await apiClient.get('/api/v1/reports');
  return response.data;
};

/**
 * Envia credenciais para obter um token de acesso.
 * @param credentials Objeto com username e password.
 */
export const login = async (credentials: LoginCredentials): Promise<{ access_token: string }> => {
  const response = await apiClient.post('/admin/login', credentials);
  return response.data;
};

/**
 * Deleta um relatório específico pelo seu ID.
 * Requer autenticação.
 * @param reportId O ID do relatório a ser deletado.
 */
export const deleteReport = async (reportId: number): Promise<void> => {
  await apiClient.delete(`/api/v1/reports/${reportId}`);
};

/**
 * Envia dois arquivos para a análise comparativa direta.
 * @param fileAntigo O arquivo mais antigo.
 * @param fileRecente O arquivo mais recente.
 */
export const uploadComparativeAnalysis = async (fileAntigo: File, fileRecente: File): Promise<{ report_url: string }> => {
  const formData = new FormData();
  formData.append('file_antigo', fileAntigo);
  formData.append('file_recente', fileRecente);

  const response = await apiClient.post('/api/v1/compare', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};