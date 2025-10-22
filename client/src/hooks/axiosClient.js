import axios from 'axios';

const axiosClient = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL}/api`,
});

// Interceptor para añadir el token de autenticación
axiosClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Interceptor para manejar respuestas y errores
axiosClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // El servidor respondió con un código de error
      if (error.response.status === 401) {
        console.error('❌ Error 401: No autorizado. Token inválido o expirado.');
        console.error('Token actual:', localStorage.getItem('authToken') ? 'Existe' : 'No existe');
        
        // Si estamos en una ruta de admin y hay 401, redirigir al login
        if (window.location.pathname.startsWith('/admin')) {
          localStorage.removeItem('authToken');
          window.location.href = '/login';
        }
      } else if (error.response.status === 403) {
        console.error('❌ Error 403: Acceso prohibido. No tienes permisos de administrador.');
      }
    }
    return Promise.reject(error);
  }
);

export default axiosClient;