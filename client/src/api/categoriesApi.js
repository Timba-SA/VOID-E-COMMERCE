import axiosClient from "../hooks/axiosClient";

export const getCategories = async () => {
    try {
        // Le sacamos el "/api" porque axiosClient ya lo tiene.
        const response = await axiosClient.get("/categories/"); // ✅ BIEN
        return response.data;
    } catch (error) {
        console.error("Error fetching categories:", error);
        throw error;
    }
};