import axiosClient from '../hooks/axiosClient';

/**
 * Crea una preferencia de pago en MercadoPago.
 * @param {object} cart - El objeto del carrito que contiene los items.
 * @param {object} shipping_address - El objeto con la dirección de envío.
 * @returns {Promise<object>} La respuesta de la API con el preference_id y el init_point.
 */
export const createCheckoutPreference = async (cart, shipping_address) => {
  try {
    // El backend ahora espera un objeto que contenga tanto el carrito como la dirección
    const payload = { cart, shipping_address };
    const response = await axiosClient.post('/checkout/create-preference', payload);
    return response.data; // Debería contener { preference_id, init_point }
  } catch (error) {
    console.error('Error creating MercadoPago preference:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};