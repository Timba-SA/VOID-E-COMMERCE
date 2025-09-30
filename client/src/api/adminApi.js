import axiosClient from '../hooks/axiosClient';

// --- User Management ---

export const getUsersAPI = async () => {
  try {
    const response = await axiosClient.get('/admin/users');
    return response.data;
  } catch (error) {
    console.error('Error fetching users:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const updateUserRoleAPI = async (userId, role) => {
  try {
    const response = await axiosClient.put(`/admin/users/${userId}/role`, { role });
    return response.data;
  } catch (error) {
    console.error(`Error updating role for user ${userId}:`, error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

// --- Order Management ---

export const getOrdersAPI = async () => {
  try {
    const response = await axiosClient.get('/admin/sales');
    return response.data;
  } catch (error) {
    console.error('Error fetching orders:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const getOrderByIdAPI = async (orderId) => {
  try {
    const response = await axiosClient.get(`/admin/sales/${orderId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching order details:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};


// --- Dashboard & Metrics ---

export const getKpisAPI = async () => {
  try {
    const response = await axiosClient.get('/admin/metrics/kpis');
    return response.data;
  } catch (error) {
    console.error('Error fetching KPIs:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const getSalesOverTimeAPI = async () => {
  try {
    const response = await axiosClient.get('/admin/charts/sales-over-time');
    return response.data;
  } catch (error) {
    console.error('Error fetching sales over time:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const getExpensesByCategoryAPI = async () => {
  try {
    const response = await axiosClient.get('/admin/charts/expenses-by-category');
    return response.data;
  } catch (error) {
    console.error('Error fetching expenses by category:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

// --- Product & Variant Management (¡ACÁ ESTÁ LO NUEVO!) ---
export const getProductVariantsAPI = async (productId) => {
  try {
    // Usamos la API pública de productos para obtener el producto y sus variantes
    const response = await axiosClient.get(`/products/${productId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching variants:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
}

export const addVariantAPI = async (productId, variantData) => {
  try {
    const response = await axiosClient.post(`/products/${productId}/variants`, variantData);
    return response.data;
  } catch (error) {
    console.error('Error adding variant:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
}

export const deleteVariantAPI = async (variantId) => {
  try {
    // Ojo que esta ruta puede variar según tu backend, la ajustamos si es necesario
    const response = await axiosClient.delete(`/admin/products/variants/${variantId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting variant:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
}