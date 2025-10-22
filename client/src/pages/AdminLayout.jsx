import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../stores/useAuthStore';

const AdminLayout = () => {
  const { t } = useTranslation();
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();

  const [isMobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="admin-dashboard-container">
      <aside className="admin-sidebar">
        
        <button 
          id="admin-menu-toggle" 
          onClick={() => setMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? t('admin_nav_close') : t('admin_nav_menu')}
        </button>

        <nav className={isMobileMenuOpen ? 'open' : ''}>
          <NavLink to="/admin" end className={({ isActive }) => isActive ? "admin-nav-link active" : "admin-nav-link"} onClick={() => setMobileMenuOpen(false)}>{t('admin_nav_dashboard')}</NavLink>
          <NavLink to="/admin/products" className={({ isActive }) => isActive ? "admin-nav-link active" : "admin-nav-link"} onClick={() => setMobileMenuOpen(false)}>{t('admin_nav_products')}</NavLink>
          <NavLink to="/admin/categories" className={({ isActive }) => isActive ? "admin-nav-link active" : "admin-nav-link"} onClick={() => setMobileMenuOpen(false)}>Categorías</NavLink>
          <NavLink to="/admin/expenses" className={({ isActive }) => isActive ? "admin-nav-link active" : "admin-nav-link"} onClick={() => setMobileMenuOpen(false)}>{t('admin_nav_expenses', 'Gastos')}</NavLink>
          <NavLink to="/admin/orders" className={({ isActive }) => isActive ? "admin-nav-link active" : "admin-nav-link"} onClick={() => setMobileMenuOpen(false)}>{t('admin_nav_orders')}</NavLink>
          <NavLink to="/admin/users" className={({ isActive }) => isActive ? "admin-nav-link active" : "admin-nav-link"} onClick={() => setMobileMenuOpen(false)}>{t('admin_nav_users')}</NavLink>
        </nav>
        <button onClick={handleLogout} className="account-logout-btn">
          {t('admin_nav_logout')}
        </button>
      </aside>
      
      <main className="admin-content">
        <Outlet />
      </main>
    </div>
  );
};

export default AdminLayout;