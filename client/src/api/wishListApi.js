// En client/src/api/wishlistApi.js
import axiosClient from '../hooks/axiosClient';

export const getWishlistAPI = async () => {
  try {
    const response = await axiosClient.get('/wishlist/');
    return response.data;
  } catch (error) {
    console.error('Error al obtener la wishlist:', error);
    throw error.response?.data || error;
  }
};

export const addToWishlistAPI = async (productId) => {
  try {
    const response = await axiosClient.post(`/wishlist/${productId}`);
    return response.data;
  } catch (error) {
    console.error('Error al añadir a la wishlist:', error);
    throw error.response?.data || error;
  }
};

export const removeFromWishlistAPI = async (productId) => {
  try {
    const response = await axiosClient.delete(`/wishlist/${productId}`);
    return response.data;
  } catch (error) {
    console.error('Error al eliminar de la wishlist:', error);
    throw error.response?.data || error;
  }
};