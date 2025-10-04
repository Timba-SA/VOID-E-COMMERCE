// En FRONTEND/vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// Sacamos 'path' porque ya no se usa de la forma antigua.
// import path from 'path'; 
import { fileURLToPath, URL } from 'url';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/', // <--- ¡¡¡ESTA ES LA LÍNEA MÁGICA!!!
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
});