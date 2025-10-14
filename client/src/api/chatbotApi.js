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

/**
 * Realiza una búsqueda inteligente de productos usando IA.
 * @param {string} query - La consulta de búsqueda.
 * @param {number} limit - Número máximo de resultados (opcional).
 * @returns {Promise<Array>} Lista de productos encontrados.
 */
export const smartSearchAPI = async (query, limit = 8) => {
  try {
    const response = await axiosClient.get('/ai-search/smart-search', {
      params: { query, limit }
    });
    return response.data;
  } catch (error) {
    console.error('Error in smart search:', error.response?.data || error.message);
    return [];
  }
};

/**
 * Obtiene recomendaciones personalizadas para un usuario.
 * @param {string} session_id - ID de sesión del usuario.
 * @param {number} limit - Número de recomendaciones (opcional).
 * @returns {Promise<Array>} Lista de productos recomendados.
 */
export const getRecommendationsAPI = async (session_id, limit = 4) => {
  try {
    const response = await axiosClient.get('/ai-search/recommendations', {
      params: { session_id, limit }
    });
    return response.data;
  } catch (error) {
    console.error('Error getting recommendations:', error.response?.data || error.message);
    return [];
  }
};

/**
 * Analiza la intención del usuario en una consulta.
 * @param {string} query - La consulta a analizar.
 * @returns {Promise<object>} Análisis de intención.
 */
export const analyzeIntentionAPI = async (query) => {
  try {
    const response = await axiosClient.post('/ai-search/analyze-intention', null, {
      params: { query }
    });
    return response.data;
  } catch (error) {
    console.error('Error analyzing intention:', error.response?.data || error.message);
    return { analysis: {}, success: false };
  }
};

/**
 * Obtiene las preferencias del usuario basadas en su historial.
 * @param {string} session_id - ID de sesión del usuario.
 * @returns {Promise<object>} Preferencias del usuario.
 */
export const getUserPreferencesAPI = async (session_id) => {
  try {
    const response = await axiosClient.get('/ai-search/user-preferences', {
      params: { session_id }
    });
    return response.data;
  } catch (error) {
    console.error('Error getting user preferences:', error.response?.data || error.message);
    return { preferences: {}, success: false };
  }
};
