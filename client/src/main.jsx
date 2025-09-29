import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './style.css';
import { CartProvider } from './context/CartContext.jsx';
import { NotificationProvider } from './context/NotificationContext.jsx';

// --- ¡ACÁ ESTÁ LA MAGIA QUE FALTA! ---
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Creamos una instancia del cliente de React Query
const queryClient = new QueryClient();
// --- FIN DE LA MAGIA ---

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* Envolvemos toda la app con el Provider que nos pedía el error */}
    <QueryClientProvider client={queryClient}>
      <NotificationProvider>
        <CartProvider>
          <App />
        </CartProvider>
      </NotificationProvider>
    </QueryClientProvider>
  </React.StrictMode>
);