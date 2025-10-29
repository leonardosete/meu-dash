import { render } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import App from "./App";

// Simula o módulo de API para que nenhuma chamada de rede real seja feita.
vi.mock("./services/api", () => ({
  getDashboardSummary: vi.fn(() =>
    Promise.resolve({
      kpi_summary: null,
      trend_history: [],
      latest_report_urls: null,
    }),
  ),
}));

describe("App", () => {
  it("renders the main app container without crashing", () => {
    const { container } = render(<App />);
    const appContainer = container.querySelector(".app-container");
    expect(appContainer).toBeInTheDocument();
  });
});