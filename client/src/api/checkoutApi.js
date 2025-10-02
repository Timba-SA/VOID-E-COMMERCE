// client/src/api/checkoutApi.js

import axiosClient from '../hooks/axiosClient';

/**
 * Crea una preferencia de pago en MercadoPago.
 * @param {object} cart - El objeto del carrito que contiene los items.
 * @param {object} shipping_address - El objeto con la dirección de envío.
 * @param {number} shippingCost - ¡El costo del envío que nos faltaba!
 * @returns {Promise<object>} La respuesta de la API con el preference_id y el init_point.
 */
export const createCheckoutPreference = async (cart, shipping_address, shippingCost) => {
  try {
    // El backend ahora espera un objeto que contenga todo
    const payload = { 
      cart, 
      shipping_address, 
      shipping_cost: shippingCost // Lo mandamos con el nombre que espera el backend
    };
    const response = await axiosClient.post('/checkout/create-preference', payload);
    return response.data;
  } catch (error) {
    console.error('Error creating MercadoPago preference:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};