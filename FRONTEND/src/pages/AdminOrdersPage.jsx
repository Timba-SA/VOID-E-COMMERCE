import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { getOrdersAPI } from '../api/adminApi'; // 1. Importar la función de API
import { NotificationContext } from '../context/NotificationContext';
import Spinner from '../components/common/Spinner';

const AdminOrdersPage = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { notify } = useContext(NotificationContext);

  useEffect(() => {
    const fetchOrders = async () => {
      setLoading(true);
      setError('');
      try {
        // 2. Usar la función de API centralizada
        const data = await getOrdersAPI();
        setOrders(Array.isArray(data) ? data : []);
      } catch (err) {
        const errorMessage = err.detail || 'No se pudieron cargar las órdenes.';
        setError(errorMessage);
        setOrders([]);
        notify(errorMessage, 'error');
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, [notify]); // El token ya no es necesario como dependencia

  if (loading) return <Spinner message="Cargando órdenes..." />;

  return (
    <div>
      <div className="admin-header">
        <h1>Gestión de Órdenes</h1>
      </div>
      
      {error && <p className="error-message" style={{color: 'red', marginBottom: '1rem'}}>{error}</p>}

      <table className="admin-table">
        <thead>
          <tr>
            <th>ID Orden</th>
            <th>ID Usuario</th>
            <th>Monto Total</th>
            <th>Estado Pago</th>
            <th>Fecha</th>
            <th>Acciones</th>
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
                    Ver Detalles
                  </Link>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="6" style={{textAlign: 'center'}}>Todavía no hay ninguna orden. ¡A vender!</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default AdminOrdersPage;
