import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import '../style.css';

const PaymentFailurePage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const paymentId = searchParams.get('payment_id');
  const status = searchParams.get('status');

  useEffect(() => {
    // Log del error de pago
    console.error('Payment failed:', { paymentId, status });
  }, [paymentId, status]);

  const handleRetryPayment = () => {
    navigate('/cart');
  };

  const handleGoHome = () => {
    navigate('/');
  };

  return (
    <div className="payment-success-container">
      <div className="payment-success-content">
        {/* Icono de error */}
        <div className="success-icon">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="#ef4444" strokeWidth="2"/>
            <path d="M15 9L9 15M9 9L15 15" stroke="#ef4444" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>

        {/* Mensaje principal */}
        <h1 className="success-title" style={{ color: '#ef4444' }}>
          {t('payment_failure_title', 'PAGO RECHAZADO')}
        </h1>

        <p className="success-message">
          {t('payment_failure_message', 'Hubo un problema al procesar tu pago. Por favor, verifica tus datos o intenta con otro método de pago.')}
        </p>

        {/* Detalles del error */}
        {paymentId && (
          <div className="order-details-box" style={{ borderColor: '#fee2e2', background: '#fef2f2' }}>
            <p>
              <strong>{t('payment_failure_payment_id', 'ID de Pago')}:</strong> {paymentId}
            </p>
            <p>
              <strong>{t('payment_failure_status', 'Estado')}:</strong> {' '}
              <span style={{ color: '#ef4444', fontWeight: 600 }}>
                {t('payment_failure_rejected', 'Rechazado')}
              </span>
            </p>
          </div>
        )}

        {/* Botones de acción */}
        <div className="success-actions">
          <button 
            className="btn-primary-success" 
            onClick={handleRetryPayment}
            style={{ background: '#ef4444' }}
          >
            {t('payment_failure_retry', 'INTENTAR NUEVAMENTE')}
          </button>
          <button 
            className="btn-secondary-success" 
            onClick={handleGoHome}
          >
            {t('payment_failure_go_home', 'VOLVER AL INICIO')}
          </button>
        </div>

        {/* Información adicional */}
        <div className="success-info">
          <p className="info-text">
            {t('payment_failure_info', 'Si el problema persiste, por favor contacta con tu entidad bancaria o intenta con otro método de pago.')}
          </p>
        </div>
      </div>
    </div>
  );
};

export default PaymentFailurePage;