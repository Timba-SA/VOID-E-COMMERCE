// client/src/api/categoriesApi.js

import axiosClient from "../hooks/axiosClient";

/**
 * Obtiene todas las categorías de productos desde la API.
 * @returns {Promise<Array>} Una lista de objetos de categoría.
 */
export const getCategories = async () => {
    try {
        // La URL correcta es /categories/, el axiosClient ya le pone el /api
        const response = await axiosClient.get("/categories/");
        
        // Nos aseguramos de devolver SIEMPRE la data, que es donde viene la lista
        return response.data;

    } catch (error) {
        console.error("Error al buscar las categorías:", error);
        // Si hay un error, lanzalo para que el componente que lo usa se entere
        throw error;
    }
};