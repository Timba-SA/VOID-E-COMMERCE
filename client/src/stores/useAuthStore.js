// En FRONTEND/src/stores/useAuthStore.js
import { create } from 'zustand';
import { jwtDecode } from 'jwt-decode';
import axiosClient from '../hooks/axiosClient'; // <-- USA EL BUENO
import { mergeCartAPI } from '../api/cartApi';

export const useAuthStore = create((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,
  isAuthLoading: true,

  fetchUser: async () => {
    try {
      // Usa el axiosClient que ya tiene la URL de Render y el token
      const response = await axiosClient.get('/auth/me');
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
      const guestSessionId = localStorage.getItem('guestSessionId');
      localStorage.setItem('authToken', token);

      if (guestSessionId) {
        await mergeCartAPI(guestSessionId);
        localStorage.removeItem('guestSessionId');
      }

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
    // LA SOLUCIÓN DEFINITIVA ESTÁ ACÁ
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