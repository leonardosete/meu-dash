/// <reference types="@testing-library/jest-dom" />
import { render, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import App from "./App";

// Simula o módulo de API para que nenhuma chamada de rede real seja feita.
// CORREÇÃO: O mock agora inclui a constante API_BASE_URL e outras funções exportadas
// para garantir que os componentes que dependem delas não quebrem.
vi.mock("./services/api", () => ({
  API_BASE_URL: "", // Fornece a constante que estava faltando
  getDashboardSummary: vi.fn(() =>
    Promise.resolve({
      kpi_summary: null,
      trend_history: [],
      latest_report_urls: null,
    }),
  ),
  getReports: vi.fn(() => Promise.resolve([])),
  login: vi.fn(() => Promise.resolve({ access_token: "test-token" })),
  deleteReport: vi.fn(() => Promise.resolve()),
  uploadStandardAnalysis: vi.fn(() => Promise.resolve({})),
  uploadComparativeAnalysis: vi.fn(() => Promise.resolve({ report_url: "" })),
}));

describe("App", () => {
  it("renders o container principal sem travar", async () => {
    const { container } = render(<App />);

    await waitFor(() => {
      const appContainer = container.querySelector(".app-container");
      expect(appContainer).not.toBeNull();
      expect(appContainer as HTMLElement).toBeInTheDocument();
    });
  });
});