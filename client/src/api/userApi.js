import axiosClient from '../hooks/axiosClient';

/**
 * Obtiene la última dirección de envío guardada para el usuario actual.
 * @returns {Promise<object>} El objeto de la dirección de envío.
 */
export const getLastAddressAPI = async () => {
  try {
    // Esta función la dejamos por si la usás en el checkout, pero ahora tenemos una mejor.
    const response = await axiosClient.get('/user/addresses');
    // Devolvemos la última del array si existe
    return response.data.length > 0 ? response.data[response.data.length - 1] : null;
  } catch (error) {
    if (error.response?.status === 404) {
      return null;
    }
    console.error('Error fetching last address:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

// --- ¡NUEVAS FUNCIONES FACHERAS! ---

/**
 * Obtiene TODAS las direcciones de envío guardadas para el usuario.
 * @returns {Promise<Array>} Un array con las direcciones del usuario.
 */
export const getAddressesAPI = async () => {
  try {
    const response = await axiosClient.get('/user/addresses');
    return response.data;
  } catch (error) {
    console.error('Error fetching addresses:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

/**
 * Guarda una nueva dirección de envío para el usuario.
 * @param {object} addressData - El objeto con los datos de la dirección.
 * @returns {Promise<object>} La respuesta de la API.
 */
export const addAddressAPI = async (addressData) => {
  try {
    const response = await axiosClient.post('/user/addresses', addressData);
    return response.data;
  } catch (error) {
    console.error('Error adding address:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};