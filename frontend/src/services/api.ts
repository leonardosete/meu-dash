import axios from "axios";
import {
  DashboardSummary,
  LoginCredentials,
  Report,
  UploadSuccessResponse,
} from "../types";

export const API_BASE_URL = "";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("meu_dash_auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    throw error;
  },
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("meu_dash_auth_token");
      window.dispatchEvent(new Event("auth-error"));
    }
    throw error;
  },
);

export const getDashboardSummary = async (): Promise<DashboardSummary> => {
  const response = await apiClient.get("/api/v1/dashboard-summary");
  return response.data;
};

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

export const getReports = async (): Promise<Report[]> => {
  const response = await apiClient.get("/api/v1/reports");
  // CORREÇÃO DEFINITIVA: Garante que qualquer URL retornada seja HTTPS.
  return response.data.map((report) => ({
    ...report,
    url: report.url.replace(/^http:/, "https"),
  }));
};

export const login = async (
  credentials: LoginCredentials,
): Promise<{ access_token: string }> => {
  const response = await apiClient.post("/admin/login", credentials);
  return response.data;
};

export const deleteReport = async (reportId: number): Promise<void> => {
  await apiClient.delete(`/api/v1/reports/${reportId}`);
};

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
  // CORREÇÃO DEFINITIVA: Garante que a URL de redirecionamento seja HTTPS.
  return {
    ...response.data,
    report_url: response.data.report_url.replace(/^http:/, "https"),
  };
};