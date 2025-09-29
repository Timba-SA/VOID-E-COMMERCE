// En FRONTEND/vite.config.js

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// ¡¡¡EL CAMBIO ESTÁ ACÁ!!!
// Importamos las herramientas nuevas para manejar rutas en ES Modules.
import { fileURLToPath, URL } from 'url'; 

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Usamos la nueva forma para decirle a Vite dónde está la carpeta 'src'.
      // Esto es compatible con "type": "module".
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
});