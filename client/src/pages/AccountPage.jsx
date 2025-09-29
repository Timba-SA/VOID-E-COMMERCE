// En FRONTEND/src/pages/AccountPage.jsx
import React, { useState, useEffect, lazy, Suspense } from 'react';
import { useAuthStore } from '../stores/useAuthStore';
import { getMyOrdersAPI } from '../api/ordersApi';
import Spinner from '../components/common/Spinner';
import { useNavigate } from 'react-router-dom';

const ProfileManagement = lazy(() => import('../components/account/ProfileManagement'));
const AddressManagement = lazy(() => import('../components/account/AddressManagement'));

const AccountPage = () => {
  const { user, logout } = useAuthStore();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState('orders');
  const navigate = useNavigate();

  useEffect(() => {
    if (activeView === 'orders') {
      setLoading(true);
      const fetchOrders = async () => {
        try {
          const data = await getMyOrdersAPI();
          setOrders(data);
        } catch (error) {
          console.error("Failed to fetch orders:", error);
        } finally {
          setLoading(false);
        }
      };
      fetchOrders();
    }
  }, [activeView]);

  const handleLogout = () => {
    // --- LA SOLUCIÓN DEFINITIVA ESTÁ AQUÍ ---
    // 1. PRIMERO, iniciamos la navegación a la página principal.
    navigate('/');
    
    // 2. DESPUÉS, envolvemos el logout en un setTimeout de 0ms.
    // Esto lo envía al final de la cola de ejecución, dándole
    // prioridad a la navegación para que comience sin ser interrumpida.
    setTimeout(() => {
      logout();
    }, 0);
  };
  
  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
        style: 'currency', currency: 'ARS',
        minimumFractionDigits: 0, maximumFractionDigits: 0,
    }).format(price).replace("ARS", "$").trim();
  };

  const renderContent = () => {
    switch (activeView) {
      case 'profile':
        return <ProfileManagement />;
      case 'addresses':
        return <AddressManagement />;
      case 'orders':
      default:
        return loading ? <Spinner message="Loading history..." /> : (
          orders.length > 0 ? (
            <table className="account-table">
              <thead>
                <tr>
                  <th>ORDER ID</th>
                  <th>DATE</th>
                  <th>TOTAL</th>
                  <th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(order => (
                  <tr key={order.id}>
                    <td>#{order.id}</td>
                    <td>{new Date(order.creado_en).toLocaleDateString('en-CA')}</td>
                    <td>{formatPrice(order.monto_total)}</td>
                    <td>
                      <span className={`status-badge status-${order.estado_pago?.toLowerCase()}`}>
                        {order.estado_pago || 'N/A'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="no-orders-message">You haven't placed any orders yet.</p>
        );
    }
  };

  return (
    <main className="account-page-container">
      <div className="account-header">
        <h1>MY ACCOUNT</h1>
      </div>
      <div className="account-content-grid">
        <aside className="account-sidebar">
          <div className="user-info">
            <h3 className="user-name">{user?.name} {user?.last_name}</h3>
            <p className="user-email">{user?.email}</p>
          </div>
          <nav className="account-nav">
            <a onClick={() => setActiveView('orders')} className={`account-nav-link ${activeView === 'orders' ? 'active' : ''}`}>Order History</a>
            <a onClick={() => setActiveView('profile')} className={`account-nav-link ${activeView === 'profile' ? 'active' : ''}`}>Profile</a>
            <a onClick={() => setActiveView('addresses')} className={`account-nav-link ${activeView === 'addresses' ? 'active' : ''}`}>Addresses</a>
          </nav>
          <button onClick={handleLogout} className="account-logout-btn">
            LOG OUT
          </button>
        </aside>

        <section className="account-main-content">
          <Suspense fallback={<Spinner />}>
            {renderContent()}
          </Suspense>
        </section>
      </div>
    </main>
  );
};

export default AccountPage;