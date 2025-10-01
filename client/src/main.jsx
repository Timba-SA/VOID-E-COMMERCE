import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './style.css';
import { CartProvider } from './context/CartContext.jsx';
import { NotificationProvider } from './context/NotificationContext.jsx';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// --- ¡ACÁ ESTÁ LA CONEXIÓN! ---
import './i18n'; 

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <NotificationProvider>
        <CartProvider>
          <App />
        </CartProvider>
      </NotificationProvider>
    </QueryClientProvider>
  </React.StrictMode>
);