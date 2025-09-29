import axiosClient from '../hooks/axiosClient';

/**
 * Envía una pregunta al chatbot y obtiene una respuesta.
 * @param {string} pregunta - La pregunta del usuario.
 * @param {string} sesion_id - El ID único de la sesión de chat.
 * @returns {Promise<object>} La respuesta del chatbot.
 */
export const postQueryAPI = async (pregunta, sesion_id) => {
  try {
    const response = await axiosClient.post('/chatbot/query', { pregunta, sesion_id });
    return response.data; // Debería contener { respuesta: "..." }
  } catch (error) {
    console.error('Error posting chatbot query:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};
