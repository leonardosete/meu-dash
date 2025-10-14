import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Redireciona requisições de /api para o servidor backend
      '/api': {
        // Dentro do Docker, os serviços se comunicam pelo nome do serviço.
        // O backend está no serviço 'backend' na porta 5000 (interna).
        target: 'http://backend:5000',
        changeOrigin: true, // Necessário para virtual hosts
        secure: false,      // Não verificar certificado SSL
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
  },
});