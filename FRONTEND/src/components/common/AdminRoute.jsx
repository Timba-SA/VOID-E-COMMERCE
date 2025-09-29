// En FRONTEND/src/components/common/AdminRoute.jsx
import React, { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { AuthContext } from '../../context/AuthContext';
import Spinner from './Spinner';

const AdminRoute = ({ children }) => {
  const { isAuthenticated, user, loading } = useContext(AuthContext);

  // Mientras se verifica la autenticación, muestra un spinner.
  if (loading) {
    return <Spinner message="Verificando credenciales..." />;
  }

  // Si el usuario está autenticado y es administrador, permite el acceso.
  if (isAuthenticated && user?.role === 'admin') {
    return children;
  }

  // Si no, redirige a la página de login.
  return <Navigate to="/login" replace />;
};

export default AdminRoute;