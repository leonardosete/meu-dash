import axios from "axios";
import {
  DashboardSummary,
  LoginCredentials,
  Report,
  UploadSuccessResponse,
} from "../types";

// CORREÇÃO: A URL base agora é uma string vazia. Isso força o Axios a fazer
// requisições relativas ao domínio atual (ex: /api/v1/...), que é o
// comportamento correto quando o frontend e o backend estão no mesmo domínio.
export const API_BASE_URL = "";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Permite o envio de cookies, se necessário para autenticação
});

// Interceptor para adicionar o token de autenticação a cada requisição, se ele existir.
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("meu_dash_auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    // Lançar o erro é a forma moderna de propagá-lo na cadeia de promessas.
    throw error;
  },
);

// Interceptor para tratar erros de resposta globalmente.
// Isso é útil para lidar com casos como tokens expirados.
apiClient.interceptors.response.use(
  (response) => response, // Se a resposta for bem-sucedida, apenas a repassa.
  (error) => {
    // Se o erro for 401 (Não Autorizado), significa que o token é inválido ou expirou.
    if (error.response && error.response.status === 401) {
      // Remove o token inválido do armazenamento local.
      localStorage.removeItem("meu_dash_auth_token");
      // Dispara um evento customizado para que a UI possa reagir ao logout.
      // Isso é menos disruptivo do que um reload forçado.
      window.dispatchEvent(new Event("auth-error"));
    }
    // Propaga o erro para que possa ser tratado pelo código que fez a chamada.
    throw error;
  },
);

/**
 * Busca os dados de resumo para o dashboard principal.
 */
export const getDashboardSummary = async (): Promise<DashboardSummary> => {
  const response = await apiClient.get("/api/v1/dashboard-summary");
  return response.data;
};

/**
 * Envia um arquivo para a análise padrão.
 * @param file O arquivo a ser enviado.
 */
export const uploadStandardAnalysis = async (
  file: File,
): Promise<UploadSuccessResponse> => {
  const formData = new FormData();
  formData.append("file_recente", file);

  const response = await apiClient.post("/api/v1/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

/**
 * Busca a lista de todos os relatórios gerados.
 */
export const getReports = async (): Promise<Report[]> => {
  const response = await apiClient.get("/api/v1/reports");
  // CORREÇÃO: Monta a URL completa no frontend usando a URL relativa da API.
  return response.data.map((report) => ({
    ...report,
    url: `${API_BASE_URL}${report.url}`,
  }));
};

/**
 * Envia credenciais para obter um token de acesso.
 * @param credentials Objeto com username e password.
 */
export const login = async (
  credentials: LoginCredentials,
): Promise<{ access_token: string }> => {
  const response = await apiClient.post("/admin/login", credentials);
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
export const uploadComparativeAnalysis = async (
  fileAntigo: File,
  fileRecente: File,
): Promise<{ report_url: string }> => {
  const formData = new FormData();
  formData.append("file_antigo", fileAntigo);
  formData.append("file_recente", fileRecente);

  const response = await apiClient.post("/api/v1/compare", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  // CORREÇÃO: Monta a URL completa no frontend.
  return {
    ...response.data,
    report_url: `${API_BASE_URL}${response.data.report_url}`,
  };
};