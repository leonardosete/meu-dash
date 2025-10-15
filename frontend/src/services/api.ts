import axios from 'axios';
import { DashboardSummary, LoginCredentials, Report } from '../types';

// A URL base da API é lida da variável de ambiente definida pelo Vite.
// Isso garante que podemos apontar para diferentes backends em dev e produção.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001';

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
  return Promise.reject(error);
});



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
export const uploadStandardAnalysis = async (file: File): Promise<any> => {
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
 * @param files Uma lista de arquivos contendo exatamente dois arquivos.
 */
export const uploadComparativeAnalysis = async (files: FileList): Promise<{ report_url: string }> => {
  const formData = new FormData();
  // O backend espera uma lista de arquivos sob a chave 'files'
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  const response = await apiClient.post('/api/v1/compare', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};