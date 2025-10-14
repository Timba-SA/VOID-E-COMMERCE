// En FRONTEND/src/pages/AdminOrderDetailPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Spinner from '../components/common/Spinner';
import axiosClient from '../hooks/axiosClient'; // Importamos axiosClient

const AdminOrderDetailPage = () => {
  const { t } = useTranslation();
  const { orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchOrderDetails = async () => {
      try {
        const response = await axiosClient.get(`/admin/sales/${orderId}`);
        setOrder(response.data);
      } catch (err) {
        setError(err.response?.data?.detail || t('admin_order_detail_load_error'));
      } finally {
        setLoading(false);
      }
    };
    fetchOrderDetails();
  }, [orderId]);

  if (loading) return <Spinner message={t('admin_order_detail_loading')} />;
  if (error) return <h2 className="error-message">{t('common_error')}: {error}</h2>;
  if (!order) return <h2>{t('admin_order_detail_not_found')}</h2>;

  return (
    <div>
      <Link to="/admin/orders">&larr; {t('admin_order_detail_back_to_orders')}</Link>
      <div className="admin-header">
        <h1>{t('admin_order_detail_title', { orderId: order.id })}</h1>
      </div>

      <div className="order-details-summary">
        <p><strong>{t('admin_order_detail_customer_id')}:</strong> {order.usuario_id}</p>
        <p><strong>{t('admin_order_detail_date')}:</strong> {new Date(order.creado_en).toLocaleString()}</p>
        <p><strong>{t('admin_order_detail_total_amount')}:</strong> ${order.monto_total}</p>
        <p><strong>{t('admin_order_detail_status')}:</strong> {order.estado_pago}</p>
      </div>

      <h3>{t('admin_order_detail_products_in_order')}</h3>
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
          {order.detalles.map(detail => (
            <tr key={detail.variante_producto_id}>
              <td>{detail.variante_producto.producto_nombre}</td>
              <td>{detail.variante_producto.tamanio} / {detail.variante_producto.color}</td>
              <td>{detail.cantidad}</td>
              <td>${detail.precio_en_momento_compra}</td>
              <td>${(detail.cantidad * detail.precio_en_momento_compra).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AdminOrderDetailPage;