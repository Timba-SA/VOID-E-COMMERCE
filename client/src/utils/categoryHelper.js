/**
 * Utilidades para manejar traducciones de categorías
 */

/**
 * Obtiene el nombre traducido de una categoría según el idioma actual
 * @param {Object} category - Objeto de categoría con nombre y nombre_i18n
 * @param {string} language - Código de idioma (es, en)
 * @returns {string} - Nombre traducido de la categoría
 */
export const getCategoryName = (category, language = 'es') => {
  if (!category) return '';
  
  // Si tiene traducciones i18n, usarlas
  if (category.nombre_i18n && typeof category.nombre_i18n === 'object') {
    // Intentar obtener el idioma solicitado
    if (category.nombre_i18n[language]) {
      return category.nombre_i18n[language];
    }
    
    // Fallback al español si el idioma no existe
    if (category.nombre_i18n['es']) {
      return category.nombre_i18n['es'];
    }
    
    // Fallback al inglés si español no existe
    if (category.nombre_i18n['en']) {
      return category.nombre_i18n['en'];
    }
  }
  
  // Si no hay traducciones, usar el nombre original
  return category.nombre || '';
};

/**
 * Obtiene todas las traducciones disponibles de una categoría
 * @param {Object} category - Objeto de categoría
 * @returns {Object} - Objeto con todas las traducciones disponibles
 */
export const getAllCategoryTranslations = (category) => {
  if (!category) return {};
  
  return category.nombre_i18n || { es: category.nombre, en: category.nombre };
};
