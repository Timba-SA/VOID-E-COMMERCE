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
    console.log('🔍 Solicitando direcciones al servidor...');
    const response = await axiosClient.get('/user/addresses');
    console.log('📦 Respuesta del servidor:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Error fetching addresses:', error.response?.data?.detail || error.message);
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
    console.log('📤 Enviando nueva dirección al servidor:', addressData);
    const response = await axiosClient.post('/user/addresses', addressData);
    console.log('✅ Respuesta del servidor (nueva dirección):', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Error adding address:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

/**
 * Actualiza una dirección de envío existente.
 * @param {string} addressId - El ID de la dirección a actualizar.
 * @param {object} addressData - El objeto con los datos actualizados de la dirección.
 * @returns {Promise<object>} La respuesta de la API.
 */
export const updateAddressAPI = async (addressId, addressData) => {
  try {
    console.log('📝 Actualizando dirección con ID:', addressId);
    console.log('📝 Nuevos datos:', addressData);
    const response = await axiosClient.put(`/user/addresses/${addressId}`, addressData);
    console.log('✅ Respuesta del servidor (actualización):', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Error updating address:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

/**
 * Elimina una dirección de envío.
 * @param {string} addressId - El ID de la dirección a eliminar.
 * @returns {Promise<object>} La respuesta de la API.
 */
export const deleteAddressAPI = async (addressId) => {
  try {
    console.log('🗑️ Eliminando dirección con ID:', addressId);
    const response = await axiosClient.delete(`/user/addresses/${addressId}`);
    console.log('✅ Respuesta del servidor (eliminación):', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Error deleting address:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};