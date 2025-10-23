import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'fs';
import { resolve } from 'path';

// Read package.json to get the version dynamically.
const packageJson = JSON.parse(readFileSync(resolve(__dirname, 'package.json'), 'utf-8'));

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Listen on all addresses, including 0.0.0.0
  },
  // Define global environment variables that will be replaced at build time.
  define: {
    // Expose the package.json version to the app via import.meta.env.
    'import.meta.env.VITE_APP_VERSION': JSON.stringify(packageJson.version),
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.ts',
  },
})