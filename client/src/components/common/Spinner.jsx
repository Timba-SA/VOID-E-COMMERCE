// En FRONTEND/src/components/common/Spinner.jsx
import React from 'react';

const Spinner = ({ message = 'Cargando...' }) => (
  <div className="spinner-container">
    <div className="spinner"></div>
    <p>{message}</p>
  </div>
);

export default Spinner;