// En FRONTEND/src/pages/AdminOrderDetailPage.jsx
import React, { useState, useEffect, useContext } from 'react';
import { useParams, Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import Spinner from '../components/common/Spinner';

const AdminOrderDetailPage = () => {
  const { orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { token } = useContext(AuthContext);

  useEffect(() => {
    const fetchOrderDetails = async () => {
      if (!token) return;
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/admin/sales/${orderId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('No se pudieron cargar los detalles de la orden.');
        const data = await response.json();
        setOrder(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchOrderDetails();
  }, [orderId, token]);

  if (loading) return <Spinner message="Cargando detalles de la orden..." />;
  if (error) return <h2 className="error-message">Error: {error}</h2>;
  if (!order) return <h2>Orden no encontrada.</h2>;

  return (
    <div>
      <Link to="/admin/orders">&larr; Volver a Órdenes</Link>
      <div className="admin-header">
        <h1>Detalle de la Orden #{order.id}</h1>
      </div>

      <div className="order-details-summary">
        <p><strong>Cliente ID:</strong> {order.usuario_id}</p>
        <p><strong>Fecha:</strong> {new Date(order.creado_en).toLocaleString()}</p>
        <p><strong>Monto Total:</strong> ${order.monto_total}</p>
        <p><strong>Estado:</strong> {order.estado_pago}</p>
      </div>

      <h3>Productos en esta Orden</h3>
      <table className="admin-table">
        <thead>
          <tr>
            <th>Producto</th>
            <th>Variante (Talle/Color)</th>
            <th>Cantidad</th>
            <th>Precio Unitario</th>
            <th>Subtotal</th>
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