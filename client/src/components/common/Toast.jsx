// En FRONTEND/src/components/common/Toast.jsx
import React, { useState, useEffect } from 'react';

const Toast = ({ message, type, onDone }) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (message) {
      setVisible(true);
      // Timer para que desaparezca solo
      const timer = setTimeout(() => {
        setVisible(false);
        // Esperamos que termine la animación de salida para limpiar el mensaje
        setTimeout(onDone, 500); 
      }, 3000); // El toast dura 3 segundos

      return () => clearTimeout(timer);
    }
  }, [message, onDone]);

  if (!message) return null;

  return (
    <div className={`toast ${type} ${visible ? 'show' : ''}`}>
      {message}
    </div>
  );
};

export default Toast;