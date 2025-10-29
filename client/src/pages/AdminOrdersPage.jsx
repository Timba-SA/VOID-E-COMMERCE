import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getOrdersAPI } from '../api/adminApi';
import { NotificationContext } from '../context/NotificationContext';
import Spinner from '../components/common/Spinner';

const AdminOrdersPage = () => {
  const { t } = useTranslation();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { notify } = useContext(NotificationContext);

  useEffect(() => {
    const fetchOrders = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await getOrdersAPI();
        setOrders(Array.isArray(data) ? data : []);
      } catch (err) {
        const errorMessage = err.detail || t('admin_orders_load_error');
        setError(errorMessage);
        setOrders([]);
        notify(errorMessage, 'error');
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, [notify]);

  if (loading) return <Spinner message={t('admin_orders_loading')} />;

  return (
    <div>
      <div className="admin-header">
        <h1>{t('admin_orders_title')}</h1>
      </div>
      
      {error && <p className="error-message" style={{color: 'red', marginBottom: '1rem'}}>{error}</p>}

      <div className="table-responsive-wrapper">
        <table className="admin-table">
          <thead>
            <tr>
              <th>{t('admin_orders_table_order_id')}</th>
              <th>{t('admin_orders_table_user_id')}</th>
              <th>{t('admin_orders_table_total')}</th>
              <th>{t('admin_orders_table_status')}</th>
              <th>{t('admin_orders_table_date')}</th>
              <th>{t('admin_orders_table_actions')}</th>
            </tr>
          </thead>
          <tbody>
            {orders.length > 0 ? (
              orders.map(order => (
                <tr key={order.id}>
                  <td>{order.id}</td>
                  <td title={order.usuario_id}>{order.usuario_id ? order.usuario_id.slice(0, 8) : 'N/A'}...</td>
                  <td>${parseFloat(order.monto_total).toLocaleString('es-AR')}</td>
                  <td>
                    <span className={`status-badge status-${order.estado_pago?.toLowerCase()}`}>
                      {order.estado_pago || 'N/A'}
                    </span>
                  </td>
                  <td>{new Date(order.creado_en).toLocaleDateString('es-AR')}</td>
                  <td className="actions-cell">
                    <Link to={`/admin/orders/${order.id}`} className="action-btn view">
                      {t('admin_orders_view_details')}
                    </Link>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="6" style={{textAlign: 'center'}}>{t('admin_orders_none')}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AdminOrdersPage;