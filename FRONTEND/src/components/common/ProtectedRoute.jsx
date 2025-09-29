import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/useAuthStore'; // 1. Importar el store de Zustand
import Spinner from './Spinner';

// El componente ahora puede aceptar un rol requerido como prop
const ProtectedRoute = ({ children, requiredRole }) => {
  // 2. Usar el store en lugar del contexto
  const { isAuthenticated, user, isAuthLoading } = useAuthStore();

  // Mientras se verifica la sesión, mostramos un spinner
  if (isAuthLoading) {
    return <Spinner message="Verificando permisos..." />;
  }

  // Si no está autenticado, redirigir al login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Si se requiere un rol específico y el usuario no lo tiene, redirigir
  if (requiredRole && user?.role !== requiredRole) {
    // Podríamos redirigir a una página de 'No autorizado' o simplemente a la home
    return <Navigate to="/" replace />;
  }

  // Si pasa todas las validaciones, renderizar el contenido protegido
  return children;
};

export default ProtectedRoute;
