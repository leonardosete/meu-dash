import { defineConfig, devices } from "@playwright/test";

/**
 * Configuração do Playwright para testes End-to-End.
 */
export default defineConfig({
  // Diretório onde os testes estão localizados.
  testDir: "./e2e",
  // Tempo máximo de execução para cada teste.
  timeout: 30 * 1000,
  expect: {
    // Tempo máximo para as asserções 'expect' esperarem.
    timeout: 5000,
  },
  use: {
    // Usa a variável de ambiente para a URL base, permitindo testar diferentes ambientes.
    // Se a variável não for definida, usa a URL de desenvolvimento local como padrão.
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://localhost:5174",
    trace: "on-first-retry",
  },
});
