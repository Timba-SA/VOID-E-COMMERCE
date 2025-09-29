import axiosClient from '../hooks/axiosClient';

/**
 * Obtiene el historial de órdenes para el usuario actualmente autenticado.
 * @returns {Promise<Array>} Una lista de las órdenes del usuario.
 */
export const getMyOrdersAPI = async () => {
  try {
    // El token de usuario se añade automáticamente por el interceptor de axiosClient
    const response = await axiosClient.get('/orders/me');
    return response.data;
  } catch (error) {
    console.error('Error fetching user orders:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};
