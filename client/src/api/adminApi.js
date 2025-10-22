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

// --- Expenses Management ---

export const getExpensesAPI = async () => {
  try {
    const response = await axiosClient.get('/admin/expenses');
    return response.data;
  } catch (error) {
    console.error('Error fetching expenses:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const createExpenseAPI = async (expenseData) => {
  try {
    const response = await axiosClient.post('/admin/expenses', expenseData);
    return response.data;
  } catch (error) {
    console.error('Error creating expense:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const deleteExpenseAPI = async (expenseId) => {
  try {
    const response = await axiosClient.delete(`/admin/expenses/${expenseId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting expense:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

// --- Charts ---

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

// --- Nuevos endpoints de gráficos ---

export const getSalesByCategoryAPI = async () => {
  try {
    const response = await axiosClient.get('/admin/charts/sales-by-category');
    return response.data;
  } catch (error) {
    console.error('Error fetching sales by category:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const getTopProductsAPI = async (limit = 5) => {
  try {
    const response = await axiosClient.get(`/admin/charts/top-products?limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching top products:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const getUserActivityAPI = async () => {
  try {
    const response = await axiosClient.get('/admin/charts/user-activity');
    return response.data;
  } catch (error) {
    console.error('Error fetching user activity:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

// --- Product & Variant Management ---
export const getProductVariantsAPI = async (productId) => {
  try {
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

// --- ¡ACÁ ESTÁ LA FUNCIÓN CORREGIDA! ---
export const deleteVariantAPI = async (variantId) => {
  try {
    // La ruta correcta que creamos en el backend
    const response = await axiosClient.delete(`/products/variants/${variantId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting variant:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
}

// --- Category Management ---
export const getCategoriesAdminAPI = async () => {
  try {
    const response = await axiosClient.get('/admin/categories');
    return response.data;
  } catch (error) {
    console.error('Error fetching categories:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const createCategoryAPI = async (categoryData) => {
  try {
    const response = await axiosClient.post('/admin/categories', categoryData);
    return response.data;
  } catch (error) {
    console.error('Error creating category:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const deleteCategoryAPI = async (categoryId) => {
  try {
    const response = await axiosClient.delete(`/admin/categories/${categoryId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting category:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};