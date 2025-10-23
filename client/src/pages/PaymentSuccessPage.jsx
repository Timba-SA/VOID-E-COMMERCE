import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getMyOrdersAPI, getOrderDetailsAPI } from '../api/ordersApi';
import Spinner from '../components/common/Spinner';
import '../style.css';

const PaymentSuccessPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [orderDetails, setOrderDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const MAX_RETRIES = 8; // Máximo 8 intentos (8 segundos)

  // Obtener parámetros de la URL
  const orderId = searchParams.get('order_id');
  const paymentId = searchParams.get('payment_id');
  const status = searchParams.get('status');
  const externalReference = searchParams.get('external_reference');
  const fromCheckout = searchParams.get('from');

  useEffect(() => {
    const fetchOrderWithRetry = async () => {
      setLoading(true);
      
      try {
        // Caso 1: Viene con order_id (nuevo flujo)
        if (orderId) {
          console.log(`🔍 Buscando orden con order_id: ${orderId}`);
          
          try {
            const order = await getOrderDetailsAPI(orderId);
            
            if (order) {
              console.log('✅ Orden encontrada:', order);
              setOrderDetails({
                paymentId: order.payment_id_mercadopago || 'Pendiente',
                status: order.estado_pago || 'pending',
                externalReference: order.id?.toString() || orderId,
                orderNumber: order.id,
                total: order.monto_total,
                createdAt: order.creado_en
              });
              setLoading(false);
            }
          } catch (error) {
            console.error('Error al buscar orden:', error);
            // Si falla, buscar última orden como fallback
            const orders = await getMyOrdersAPI();
            if (orders && orders.length > 0) {
              const lastOrder = orders[0];
              setOrderDetails({
                paymentId: lastOrder.payment_id_mercadopago || 'N/A',
                status: lastOrder.estado_pago || 'pending',
                externalReference: lastOrder.id?.toString() || 'N/A',
                orderNumber: lastOrder.id,
                total: lastOrder.monto_total,
                createdAt: lastOrder.fecha_creacion
              });
            }
            setLoading(false);
          }
        } 
        // Caso 2: Viene desde checkout sin order_id - buscar última orden
        else if (fromCheckout === 'checkout') {
          console.log('🔍 Buscando última orden del usuario...');
          const orders = await getMyOrdersAPI();
          
          if (orders && orders.length > 0) {
            const lastOrder = orders[0];
            setOrderDetails({
              paymentId: lastOrder.payment_id_mercadopago || 'N/A',
              status: lastOrder.estado_pago || 'pending',
              externalReference: lastOrder.id?.toString() || 'N/A',
              orderNumber: lastOrder.id,
              total: lastOrder.monto_total,
              createdAt: lastOrder.fecha_creacion
            });
          }
          setLoading(false);
        } 
        // Caso 3: Sin parámetros válidos - redirigir
        else {
          console.log('❌ No hay parámetros válidos, redirigiendo...');
          navigate('/');
        }
      } catch (error) {
        console.error('Error al cargar orden:', error);
        setLoading(false);
      }
    };

    fetchOrderWithRetry();
  }, [orderId, paymentId, status, externalReference, fromCheckout, navigate, retryCount]);

  const handleGoHome = () => {
    navigate('/');
  };

  const handleViewOrders = () => {
    navigate('/account');
  };

  if (loading) {
    return <Spinner message={t('payment_verifying', 'Verificando tu pago...')} />;
  }

  return (
    <div className="payment-success-container">
      <div className="payment-success-content">
        {/* Icono de éxito */}
        <div className="success-icon">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="#22c55e" strokeWidth="2"/>
            <path d="M8 12.5L10.5 15L16 9.5" stroke="#22c55e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>

        {/* Mensaje principal */}
        <h1 className="success-title">
          {t('payment_success_title', '¡COMPRA EXITOSA!')}
        </h1>

        <p className="success-message">
          {t('payment_success_message', 'Tu pedido ha sido procesado correctamente. Recibirás un email de confirmación con los detalles de tu compra.')}
        </p>

        {/* Detalles del pago */}
        {orderDetails && (
          <div className="order-details-box">
            <h3>{t('payment_success_order_details', 'Detalles del Pedido')}</h3>
            {orderDetails.orderNumber && (
              <p>
                <strong>{t('payment_success_order_number', 'Número de Orden')}:</strong> #{orderDetails.orderNumber}
              </p>
            )}
            {orderDetails.paymentId && (
              <p>
                <strong>{t('payment_success_payment_id', 'ID de Pago')}:</strong> {orderDetails.paymentId}
              </p>
            )}
            {orderDetails.total && (
              <p>
                <strong>{t('payment_total', 'Total Pagado')}:</strong> ${orderDetails.total.toFixed(2)}
              </p>
            )}
            <p>
              <strong>{t('payment_success_status', 'Estado')}:</strong> {' '}
              <span className="status-approved">
                {orderDetails.status === 'approved' ? t('payment_success_approved', 'Aprobado') : t('payment_pending', 'Pendiente')}
              </span>
            </p>
            {orderDetails.externalReference && orderDetails.externalReference !== 'N/A' && !orderDetails.orderNumber && (
              <p className="text-sm text-gray-500">
                <strong>{t('payment_reference', 'Referencia')}:</strong> {orderDetails.externalReference}
              </p>
            )}
          </div>
        )}

        {/* Botones de acción */}
        <div className="success-actions">
          <button 
            className="btn-primary-success" 
            onClick={handleGoHome}
          >
            {t('payment_success_go_home', 'VOLVER AL INICIO')}
          </button>
          <button 
            className="btn-secondary-success" 
            onClick={handleViewOrders}
          >
            {t('payment_success_view_orders', 'VER MIS PEDIDOS')}
          </button>
        </div>

        {/* Información adicional */}
        <div className="success-info">
          <p className="info-text">
            {t('payment_success_info', 'Si tienes alguna consulta sobre tu pedido, puedes contactarnos en cualquier momento.')}
          </p>
        </div>
      </div>
    </div>
  );
};

export default PaymentSuccessPage;