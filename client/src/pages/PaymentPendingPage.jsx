import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import '../style.css';

const PaymentPendingPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const paymentId = searchParams.get('payment_id');
  const status = searchParams.get('status');

  useEffect(() => {
    console.log('Payment pending:', { paymentId, status });
  }, [paymentId, status]);

  const handleGoHome = () => {
    navigate('/');
  };

  const handleViewOrders = () => {
    navigate('/account');
  };

  return (
    <div className="payment-success-container">
      <div className="payment-success-content">
        {/* Icono de pendiente */}
        <div className="success-icon">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="#f59e0b" strokeWidth="2"/>
            <path d="M12 8V12L14 14" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>

        {/* Mensaje principal */}
        <h1 className="success-title" style={{ color: '#f59e0b' }}>
          {t('payment_pending_title', 'PAGO PENDIENTE')}
        </h1>

        <p className="success-message">
          {t('payment_pending_message', 'Tu pago está siendo procesado. Te notificaremos por email cuando se complete la transacción.')}
        </p>

        {/* Detalles del pago */}
        {paymentId && (
          <div className="order-details-box" style={{ borderColor: '#fef3c7', background: '#fffbeb' }}>
            <p>
              <strong>{t('payment_pending_payment_id', 'ID de Pago')}:</strong> {paymentId}
            </p>
            <p>
              <strong>{t('payment_pending_status', 'Estado')}:</strong> {' '}
              <span style={{ color: '#f59e0b', fontWeight: 600 }}>
                {t('payment_pending_processing', 'En Proceso')}
              </span>
            </p>
          </div>
        )}

        {/* Botones de acción */}
        <div className="success-actions">
          <button 
            className="btn-primary-success" 
            onClick={handleGoHome}
            style={{ background: '#f59e0b' }}
          >
            {t('payment_pending_go_home', 'VOLVER AL INICIO')}
          </button>
          <button 
            className="btn-secondary-success" 
            onClick={handleViewOrders}
            style={{ borderColor: '#f59e0b', color: '#f59e0b' }}
          >
            {t('payment_pending_view_orders', 'VER MIS PEDIDOS')}
          </button>
        </div>

        {/* Información adicional */}
        <div className="success-info">
          <p className="info-text">
            {t('payment_pending_info', 'El proceso puede tardar unos minutos. Recibirás una notificación por email cuando tu pago sea confirmado.')}
          </p>
        </div>
      </div>
    </div>
  );
};

export default PaymentPendingPage;