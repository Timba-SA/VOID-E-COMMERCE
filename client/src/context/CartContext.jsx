import React, { createContext, useState, useEffect, useContext } from 'react';
import { useAuthStore } from '../stores/useAuthStore'; // 1. Usar el store de Zustand
import { NotificationContext } from './NotificationContext';
import { fetchCartAPI, addItemToCartAPI, removeItemFromCartAPI, getGuestSessionAPI } from '../api/cartApi'; // 2. Importar las nuevas funciones de API

export const CartContext = createContext();

export const CartProvider = ({ children }) => {
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // 3. Obtener el estado de autenticación del store
  const { isAuthenticated } = useAuthStore(); 
  const { notify } = useContext(NotificationContext);

  const fetchCart = async () => {
    setLoading(true);
    try {
      // La lógica de headers ahora está encapsulada en cartApi.js
      const cartData = await fetchCartAPI();
      setCart(cartData);
    } catch (error) {
      console.error("Error al obtener el carrito:", error);
      notify('Error al cargar el carrito', 'error');
    } finally {
      setLoading(false);
    }
  };

  // 4. El efecto ahora depende del estado de autenticación del store
  useEffect(() => {
    // Asegurarse de que el ID de invitado exista al cargar
    const ensureGuestId = async () => {
      const token = localStorage.getItem('authToken');
      let guestId = localStorage.getItem('guestSessionId');
      if (!token && !guestId) {
        try {
          const data = await getGuestSessionAPI();
          localStorage.setItem('guestSessionId', data.guest_session_id);
        } catch (error) {
          console.error('No se pudo crear sesión de invitado.', error);
        }
      }
    };

    ensureGuestId().then(() => {
        fetchCart();
    });
  }, [isAuthenticated]);

  const addItemToCart = async (item) => {
    try {
      const updatedCart = await addItemToCartAPI(item);
      setCart(updatedCart);
      notify('Producto añadido al carrito', 'success');
    } catch (error) {
      console.error("Error al agregar item:", error);
      notify(error.message || "No se pudo agregar el producto.", 'error');
    }
  };

  const removeItemFromCart = async (variante_id) => {
    try {
      const updatedCart = await removeItemFromCartAPI(variante_id);
      setCart(updatedCart);
      notify('Producto eliminado del carrito.', 'success');
    } catch (error) {
      console.error("Error al eliminar item:", error);
      notify(error.message || "No se pudo eliminar el producto.", 'error');
    }
  };

  const value = {
    cart,
    loading,
    fetchCart, // Exponer fetchCart para poder refrescar el carrito manualmente si es necesario
    itemCount: cart?.items?.reduce((total, item) => total + item.quantity, 0) || 0,
    addItemToCart,
    removeItemFromCart,
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};
