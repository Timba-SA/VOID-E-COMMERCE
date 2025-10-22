// En FRONTEND/src/pages/AccountPage.jsx
import React, { useState, useEffect, lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next'; // Importar
import { useAuthStore } from '../stores/useAuthStore';
import { getMyOrdersAPI } from '../api/ordersApi';
import Spinner from '../components/common/Spinner';
import { useNavigate } from 'react-router-dom';

const ProfileManagement = lazy(() => import('../components/account/ProfileManagement'));
const AddressManagement = lazy(() => import('../components/account/AddressManagement'));
const OrderHistory = lazy(() => import('../components/account/OrderHistory'));

const AccountPage = () => {
  const { t } = useTranslation(); // Inicializar
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
    navigate('/');
    setTimeout(() => {
      logout();
    }, 0);
  };

  const renderContent = () => {
    switch (activeView) {
      case 'profile':
        return <ProfileManagement />;
      case 'addresses':
        return <AddressManagement />;
      case 'orders':
      default:
        return <OrderHistory orders={orders} loading={loading} />;
    }
  };

  return (
    <main className="account-page-container">
      <div className="account-header">
        <h1>{t('account_title')}</h1>
      </div>
      <div className="account-content-grid">
        <aside className="account-sidebar">
          <div className="user-info">
            <h3 className="user-name">{user?.name} {user?.last_name}</h3>
            <p className="user-email">{user?.email}</p>
          </div>
          <nav className="account-nav">
            <a onClick={() => setActiveView('orders')} className={`account-nav-link ${activeView === 'orders' ? 'active' : ''}`}>{t('account_order_history')}</a>
            <a onClick={() => setActiveView('profile')} className={`account-nav-link ${activeView === 'profile' ? 'active' : ''}`}>{t('account_profile')}</a>
            <a onClick={() => setActiveView('addresses')} className={`account-nav-link ${activeView === 'addresses' ? 'active' : ''}`}>{t('account_addresses')}</a>
          </nav>
          <button onClick={handleLogout} className="account-logout-btn">
            {t('account_logout_button')}
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