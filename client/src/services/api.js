// En FRONTEND/src/services/api.js
import axios from 'axios';

const axiosClient = axios.create({
  baseURL: 'http://localhost:8000/api',
});

axiosClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// --- Funciones Públicas ---
export const getProducts = (limit = 100) => axiosClient.get(`/products?limit=${limit}`).then(res => res.data);
export const getProductById = (id) => axiosClient.get(`/products/${id}`).then(res => res.data);
export const searchProducts = (query) => axiosClient.get(`/products/search?q=${query}`).then(res => res.data);
export const loginUser = (formData) => axiosClient.post('/auth/login', formData, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }).then(res => res.data);
export const registerUser = (payload) => axiosClient.post('/auth/register', payload).then(res => res.data);

// --- Funciones de Carrito ---
export const getCart = () => axiosClient.get('/cart/').then(res => res.data);
export const addItemToCart = (item) => axiosClient.post('/cart/items', item).then(res => res.data);
export const removeItemFromCart = (variante_id) => axiosClient.delete(`/cart/items/${variante_id}`).then(res => res.data);

// --- Funciones de ADMIN ---
export const getAdminKpis = () => axiosClient.get('/admin/metrics/kpis').then(res => res.data);
export const getAdminSalesChart = () => axiosClient.get('/admin/charts/sales-over-time').then(res => res.data.data);
export const getAdminUsers = () => axiosClient.get('/admin/users').then(res => res.data);
export const getAdminOrders = () => axiosClient.get('/admin/sales').then(res => res.data);
export const getAdminOrderDetail = (orderId) => axiosClient.get(`/admin/sales/${orderId}`).then(res => res.data);
export const updateAdminUserRole = ({ userId, role }) => axiosClient.put(`/admin/users/${userId}/role`, { role });
export const deleteAdminProduct = (productId) => axiosClient.delete(`/products/${productId}`);
export const addAdminVariant = ({ productId, variantData }) => axiosClient.post(`/products/${productId}/variants`, variantData).then(res => res.data);
export const deleteAdminVariant = (variantId) => axiosClient.delete(`/products/variants/${variantId}`);

// --- Chatbot y Checkout ---
export const postChatQuery = (payload) => axiosClient.post('/chatbot/query', payload).then(res => res.data);
export const createMercadoPagoPreference = (cart) => axiosClient.post('/checkout/create_preference', cart).then(res => res.data);