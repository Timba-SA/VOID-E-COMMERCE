// En FRONTEND/src/context/CartContext.jsx
import React, { createContext, useState, useEffect, useContext } from 'react';
import { useAuthStore } from '../stores/useAuthStore';
import { NotificationContext } from './NotificationContext';
import { fetchCartAPI, addItemToCartAPI, removeItemFromCartAPI, getGuestSessionAPI, updateItemQuantityAPI } from '../api/cartApi'; // <-- ¡Importamos la nueva!

export const CartContext = createContext();

export const CartProvider = ({ children }) => {
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const { isAuthenticated } = useAuthStore(); 
  const { notify } = useContext(NotificationContext);

  const fetchCart = async () => {
    setLoading(true);
    try {
      const cartData = await fetchCartAPI();
      setCart(cartData);
    } catch (error) {
      console.error("Error al obtener el carrito:", error);
      notify('Error al cargar el carrito', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
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
      // notify('Producto añadido al carrito', 'success'); // <-- ¡ACÁ ESTÁ CALLADITO LA BOCA!
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
  
  // --- ¡NUEVA FUNCIÓN PARA EL CONTEXTO! ---
  const updateItemQuantity = async (variante_id, quantity) => {
    if (quantity <= 0) {
      // Si la cantidad es 0 o menos, mejor lo borramos.
      removeItemFromCart(variante_id);
      return;
    }
    try {
      const updatedCart = await updateItemQuantityAPI(variante_id, quantity);
      setCart(updatedCart);
      // No ponemos notificación acá para que no sea molesto
    } catch (error) {
      console.error("Error al actualizar la cantidad:", error);
      notify(error.message || "No se pudo actualizar la cantidad.", 'error');
    }
  };


  const value = {
    cart,
    loading,
    fetchCart,
    itemCount: cart?.items?.reduce((total, item) => total + item.quantity, 0) || 0,
    addItemToCart,
    removeItemFromCart,
    updateItemQuantity, // <-- La agregamos acá para que esté disponible en toda la app
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};