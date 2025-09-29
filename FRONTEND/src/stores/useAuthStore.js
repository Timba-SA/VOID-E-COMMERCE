// En FRONTEND/src/stores/useAuthStore.js
import { create } from 'zustand';
import { jwtDecode } from 'jwt-decode';
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);


export const useAuthStore = create((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,
  isAuthLoading: true,

  fetchUser: async () => {
    try {
      const response = await api.get('/auth/me');
      set({ user: response.data });
      return response.data;
    } catch (error) {
      console.error('Error fetching user data:', error);
      set({ token: null, user: null, isAuthenticated: false });
      localStorage.removeItem('authToken');
      return null;
    }
  },

  login: async (token) => {
    try {
      localStorage.setItem('authToken', token);
      
      const user = await useAuthStore.getState().fetchUser();
      if (user) {
        set({ token, isAuthenticated: true });
      } else {
        throw new Error('Could not fetch user data');
      }
      
    } catch (error) {
      console.error("Fallo al decodificar el token o al obtener el usuario:", error);
    }
  },

  logout: () => {
    localStorage.removeItem('authToken');
    // --- LA SOLUCIÓN DEFINITIVA ESTÁ ACÁ ---
    // Al cerrar sesión, también eliminamos el ID del carrito de invitado.
    localStorage.removeItem('guestSessionId');
    // ------------------------------------
    set({ token: null, user: null, isAuthenticated: false, isAuthLoading: false });
  },

  checkAuth: async () => { 
    const token = localStorage.getItem('authToken');
    if (token) {
      try {
        const decodedUser = jwtDecode(token);
        if (decodedUser.exp * 1000 > Date.now()) {
          const user = await useAuthStore.getState().fetchUser();
          if (user) {
            set({ token, isAuthenticated: true });
          }
        } else {
          localStorage.removeItem('authToken');
        }
      } catch (error) {
        localStorage.removeItem('authToken');
      }
    }
    set({ isAuthLoading: false });
  },
}));