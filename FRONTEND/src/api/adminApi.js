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

export const getProductMetricsAPI = async () => {
  try {
    const response = await axiosClient.get('/admin/metrics/products');
    return response.data;
  } catch (error) {
    console.error('Error fetching product metrics:', error.response?.data?.detail || error.message);
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
