import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync } from "fs";
import { resolve } from "path";

// Read package.json to get the version dynamically.
const packageJson = JSON.parse(
  readFileSync(resolve(__dirname, "package.json"), "utf-8"),
);

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Listen on all addresses, including 0.0.0.0
    proxy: {
      // Redireciona todas as chamadas de API para o backend
      "/api": {
        target: "http://backend:5000",
      },
      // CORREÇÃO: Adiciona a regra de proxy para as rotas de administração
      "/admin": {
        target: "http://backend:5000",
      },
      // Redireciona o acesso à documentação do Flasgger
      "/apidocs": {
        target: "http://backend:5000",
      },
      // **CORREÇÃO:** Redireciona o acesso aos arquivos estáticos do Flasgger
      "/flasgger_static": {
        target: "http://backend:5000",
      },
      // Redireciona o acesso aos relatórios gerados
      "/reports": {
        target: "http://backend:5000",
      },
      // Redireciona o acesso à documentação estática
      "/docs": {
        target: "http://backend:5000",
      },
    },
  },
  // Define global environment variables that will be replaced at build time.
  define: {
    // Expose the package.json version to the app via import.meta.env.
    "import.meta.env.VITE_APP_VERSION": JSON.stringify(packageJson.version),
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/setupTests.ts",
  },
});