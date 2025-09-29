import axiosClient from '../hooks/axiosClient';

// Helper para obtener los headers correctos (token o ID de invitado)
const getCartHeaders = () => {
  const headers = {};
  // El token de usuario lo añade el interceptor de axiosClient automáticamente.
  // Solo necesitamos añadir el ID de invitado si no hay token.
  const token = localStorage.getItem('authToken');
  if (!token) {
    const guestId = localStorage.getItem('guestSessionId'); // Usamos 'guestSessionId' para consistencia
    if (guestId) {
      headers['X-Guest-Session-ID'] = guestId;
    }
  }
  return headers;
};

export const fetchCartAPI = async () => {
  try {
    const response = await axiosClient.get('/cart/', { headers: getCartHeaders() });
    return response.data;
  } catch (error) {
    console.error('Error fetching cart:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const addItemToCartAPI = async (item) => {
  // item = { variante_id: ..., quantity: ... }
  try {
    const response = await axiosClient.post('/cart/items', item, { headers: getCartHeaders() });
    return response.data;
  } catch (error) {
    console.error('Error adding item to cart:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const removeItemFromCartAPI = async (varianteId) => {
  try {
    const response = await axiosClient.delete(`/cart/items/${varianteId}`, { headers: getCartHeaders() });
    return response.data;
  } catch (error) {
    console.error('Error removing item from cart:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const getGuestSessionAPI = async () => {
  try {
    const response = await axiosClient.get('/cart/session/guest');
    return response.data;
  } catch (error) {
    console.error('Error getting guest session:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const mergeCartAPI = async (guestSessionId) => {
  try {
    const response = await axiosClient.post('/auth/merge-cart', {
      guest_session_id: guestSessionId,
    });
    console.log('Cart merged successfully', response.data);
    return response.data;
  } catch (error) {
    console.error('Error merging cart:', error.response?.data?.detail || error.message);
    // No se relanza el error para no bloquear el flujo de login.
  }
};
