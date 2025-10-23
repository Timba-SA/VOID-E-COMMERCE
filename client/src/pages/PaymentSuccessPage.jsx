import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getMyOrdersAPI, getOrderDetailsAPI, getOrderByPaymentIdAPI } from '../api/ordersApi';
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
        // Obtener todos los parámetros posibles que MP puede enviar
        const collectionId = searchParams.get('collection_id'); // MP también envía esto como payment_id
        const merchantOrderId = searchParams.get('merchant_order_id');
        const preferenceId = searchParams.get('preference_id');
        const collectionStatus = searchParams.get('collection_status');
        
        console.log('📋 Parámetros de URL:', {
          paymentId,
          collectionId,
          orderId,
          status,
          collectionStatus,
          externalReference,
          merchantOrderId,
          preferenceId
        });
        
        // Caso 1: Viene desde Mercado Pago con payment_id o collection_id
        const finalPaymentId = paymentId || collectionId;
        
        if (finalPaymentId) {
          console.log(`🔍 Buscando orden con payment_id: ${finalPaymentId}`);
          
          try {
            const order = await getOrderByPaymentIdAPI(finalPaymentId);
            
            if (order) {
              console.log('✅ Orden encontrada por payment_id:', order);
              setOrderDetails({
                paymentId: order.payment_id_mercadopago || finalPaymentId,
                status: order.estado_pago || 'Aprobado',
                externalReference: order.id?.toString() || externalReference,
                orderNumber: order.id,
                total: order.monto_total,
                createdAt: order.creado_en
              });
              setLoading(false);
              return;
            }
          } catch (error) {
            console.error('Error al buscar orden por payment_id:', error);
          }
        }
        
        // Caso 2: Viene con order_id directo
        if (orderId) {
          console.log(`🔍 Buscando orden con order_id: ${orderId}`);
          
          try {
            const order = await getOrderDetailsAPI(orderId);
            
            if (order) {
              console.log('✅ Orden encontrada por order_id:', order);
              setOrderDetails({
                paymentId: order.payment_id_mercadopago || 'N/A',
                status: order.estado_pago || 'Aprobado',
                externalReference: order.id?.toString() || orderId,
                orderNumber: order.id,
                total: order.monto_total,
                createdAt: order.creado_en
              });
              setLoading(false);
              return;
            }
          } catch (error) {
            console.error('Error al buscar orden:', error);
          }
        }
        
        // Caso 3: Buscar última orden del usuario (fallback confiable)
        console.log('🔍 Buscando última orden del usuario...');
        const orders = await getMyOrdersAPI();
        
        if (orders && orders.length > 0) {
          const lastOrder = orders[0];
          console.log('✅ Última orden encontrada:', lastOrder);
          setOrderDetails({
            paymentId: lastOrder.payment_id_mercadopago || 'N/A',
            status: lastOrder.estado_pago || 'Aprobado',
            externalReference: lastOrder.id?.toString() || 'N/A',
            orderNumber: lastOrder.id,
            total: lastOrder.monto_total,
            createdAt: lastOrder.fecha_creacion
          });
        } else {
          // Sin órdenes - redirigir
          console.log('❌ No se encontraron órdenes, redirigiendo...');
          setTimeout(() => navigate('/'), 3000);
        }
        
        setLoading(false);
      } catch (error) {
        console.error('Error al cargar orden:', error);
        setLoading(false);
      }
    };

    fetchOrderWithRetry();
  }, [orderId, paymentId, status, externalReference, fromCheckout, navigate, retryCount, searchParams]);

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
        {/* Icono dinámico según el estado */}
        <div className="success-icon">
          {orderDetails && orderDetails.status === 'Aprobado' ? (
            // Icono de éxito (verde)
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="#22c55e" strokeWidth="2"/>
              <path d="M8 12.5L10.5 15L16 9.5" stroke="#22c55e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          ) : (
            // Icono de advertencia (amarillo/naranja)
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="#f59e0b" strokeWidth="2"/>
              <path d="M12 8V12" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="12" cy="16" r="1" fill="#f59e0b"/>
            </svg>
          )}
        </div>

        {/* Mensaje principal dinámico */}
        <h1 className="success-title">
          {orderDetails && orderDetails.status === 'Aprobado' 
            ? t('payment_success_title', '¡COMPRA EXITOSA!') 
            : t('payment_pending_title', 'PAGO PENDIENTE')}
        </h1>

        <p className="success-message">
          {orderDetails && orderDetails.status === 'Aprobado' 
            ? t('payment_success_message', 'Tu pedido ha sido procesado correctamente. Recibirás un email de confirmación con los detalles de tu compra.')
            : t('payment_pending_message', 'Tu pedido está registrado, pero el pago aún no ha sido confirmado. Por favor, completa el pago en Mercado Pago para que podamos procesar tu orden.')}
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
            {orderDetails.paymentId && orderDetails.paymentId !== 'Pendiente' && orderDetails.paymentId !== 'N/A' && (
              <p>
                <strong>{t('payment_success_payment_id', 'ID de Pago')}:</strong> {orderDetails.paymentId}
              </p>
            )}
            {orderDetails.total && (
              <p>
                <strong>{t('payment_total', 'Total')}:</strong> ${orderDetails.total.toFixed(2)}
              </p>
            )}
            <p>
              <strong>{t('payment_success_status', 'Estado')}:</strong> {' '}
              <span className={orderDetails.status === 'Aprobado' ? 'status-approved' : 'status-pending'}>
                {orderDetails.status === 'Aprobado' 
                  ? t('payment_success_approved', 'Aprobado') 
                  : t('payment_pending', 'Pendiente de Pago')}
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
            {orderDetails && orderDetails.status === 'Aprobado'
              ? t('payment_success_info', 'Si tienes alguna consulta sobre tu pedido, puedes contactarnos en cualquier momento.')
              : t('payment_pending_info', 'Una vez que completes el pago, tu pedido será procesado automáticamente. Puedes verificar el estado en "Mis Pedidos".')}
          </p>
        </div>
      </div>
    </div>
  );
};

export default PaymentSuccessPage;