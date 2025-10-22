// En FRONTEND/src/pages/AdminOrderDetailPage.jsx
import React, { useState, useEffect, useContext } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getOrderByIdAPI } from '../api/adminApi';
import { NotificationContext } from '../context/NotificationContext';
import Spinner from '../components/common/Spinner';

const AdminOrderDetailPage = () => {
  const { t } = useTranslation();
  const { orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { notify } = useContext(NotificationContext);

  useEffect(() => {
    const fetchOrderDetails = async () => {
      setLoading(true);
      setError('');
      try {
        console.log('🔵 Buscando orden con ID:', orderId);
        const data = await getOrderByIdAPI(orderId);
        console.log('✅ Orden encontrada:', data);
        setOrder(data);
      } catch (err) {
        const errorMessage = err.detail || err.response?.data?.detail || t('admin_order_detail_load_error');
        console.error('❌ Error al cargar orden:', errorMessage);
        setError(errorMessage);
        notify(errorMessage, 'error');
      } finally {
        setLoading(false);
      }
    };
    
    if (orderId) {
      fetchOrderDetails();
    }
  }, [orderId, notify]);

  if (loading) return <Spinner message={t('admin_order_detail_loading')} />;
  if (error) return (
    <div>
      <Link to="/admin/orders" className="back-link">&larr; {t('admin_order_detail_back_to_orders')}</Link>
      <h2 className="error-message" style={{ color: 'red', marginTop: '2rem' }}>
        {t('common_error')}: {error}
      </h2>
    </div>
  );
  if (!order) return (
    <div>
      <Link to="/admin/orders" className="back-link">&larr; {t('admin_order_detail_back_to_orders')}</Link>
      <h2 style={{ marginTop: '2rem' }}>{t('admin_order_detail_not_found')}</h2>
    </div>
  );

  return (
    <div>
      <Link to="/admin/orders" className="back-link">&larr; {t('admin_order_detail_back_to_orders')}</Link>
      <div className="admin-header">
        <h1>{t('admin_order_detail_title', { orderId: order.id })}</h1>
      </div>

      <div className="order-details-summary" style={{ 
        backgroundColor: '#f8f9fa', 
        padding: '1.5rem', 
        borderRadius: '4px', 
        marginBottom: '2rem',
        border: '1px solid #dee2e6'
      }}>
        <p><strong>{t('admin_order_detail_customer_id')}:</strong> {order.usuario_id}</p>
        <p><strong>{t('admin_order_detail_date')}:</strong> {new Date(order.creado_en).toLocaleString('es-AR')}</p>
        <p><strong>{t('admin_order_detail_total_amount')}:</strong> ${parseFloat(order.monto_total).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
        <p>
          <strong>{t('admin_order_detail_status')}:</strong>{' '}
          <span className={`status-badge status-${order.estado_pago?.toLowerCase()}`}>
            {order.estado_pago || 'N/A'}
          </span>
        </p>
      </div>

      <h3 style={{ marginBottom: '1rem' }}>{t('admin_order_detail_products_in_order')}</h3>
      <div className="table-responsive-wrapper">
        <table className="admin-table">
          <thead>
            <tr>
              <th>{t('admin_order_detail_table_product')}</th>
              <th>{t('admin_order_detail_table_variant')}</th>
              <th>{t('admin_order_detail_table_quantity')}</th>
              <th>{t('admin_order_detail_table_unit_price')}</th>
              <th>{t('admin_order_detail_table_subtotal')}</th>
            </tr>
          </thead>
          <tbody>
            {order.detalles && order.detalles.length > 0 ? (
              order.detalles.map((detail, index) => (
                <tr key={`${detail.variante_producto_id}-${index}`}>
                  <td>{detail.variante_producto?.producto_nombre || 'N/A'}</td>
                  <td>{detail.variante_producto?.tamanio || 'N/A'} / {detail.variante_producto?.color || 'N/A'}</td>
                  <td>{detail.cantidad}</td>
                  <td>${parseFloat(detail.precio_en_momento_compra).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                  <td>${(detail.cantidad * parseFloat(detail.precio_en_momento_compra)).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" style={{ textAlign: 'center' }}>No hay productos en esta orden</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AdminOrderDetailPage;