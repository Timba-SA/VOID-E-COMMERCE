import React from 'react';
import { Link } from 'react-router-dom';

const PaymentPendingPage = () => (
  <div className="payment-status-page">
    <div className="status-icon pending">!</div>
    <h1>Pago Pendiente</h1>
    <p>Tu pago está siendo procesado. Te notificaremos por email cuando se apruebe.</p>
    <Link to="/" className="form-button outline">Volver al Inicio</Link>
  </div>
);
export default PaymentPendingPage;