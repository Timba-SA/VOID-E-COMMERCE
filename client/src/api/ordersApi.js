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

/**
 * Obtiene los detalles completos de una orden específica del usuario.
 * @param {number} orderId - ID de la orden
 * @returns {Promise<Object>} Los detalles completos de la orden incluyendo productos
 */
export const getOrderDetailsAPI = async (orderId) => {
  try {
    const response = await axiosClient.get(`/orders/me/${orderId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching order details:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

/**
 * Busca una orden por su payment_id de Mercado Pago.
 * Útil para obtener la orden recién procesada después de un pago.
 * @param {string} paymentId - ID del pago de Mercado Pago
 * @returns {Promise<Object|null>} La orden si existe, null si aún no ha sido procesada
 */
export const getOrderByPaymentIdAPI = async (paymentId) => {
  try {
    const response = await axiosClient.get(`/orders/by-payment/${paymentId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching order by payment ID:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};
