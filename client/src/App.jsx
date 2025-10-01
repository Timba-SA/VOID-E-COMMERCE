// client/src/App.jsx

import React, { useState, useEffect, lazy, Suspense, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';
import { useAuthStore } from './stores/useAuthStore';
import Navbar from '@/components/common/Navbar.jsx';
import Footer from '@/components/common/Footer.jsx';
import DropdownMenu from '@/components/common/DropdownMenu.jsx';
import ProtectedRoute from '@/components/common/ProtectedRoute.jsx';
import CartNotificationModal from '@/components/products/CartNotificationModal.jsx';
import SearchModal from '@/components/common/SearchModal.jsx';
import Chatbot from '@/components/common/Chatbot.jsx';
import Spinner from '@/components/common/Spinner.jsx';

// --- Páginas ---
const HomePage = lazy(() => import('@/pages/HomePage.jsx'));
const LoginPage = lazy(() => import('@/pages/LoginPage.jsx'));
const RegisterPage = lazy(() => import('@/pages/RegisterPage.jsx'));
const ProductPage = lazy(() => import('@/pages/ProductPage.jsx'));
const CartPage = lazy(() => import('@/pages/CartPage.jsx'));
const CheckoutPage = lazy(() => import('@/pages/CheckoutPage.jsx'));
const SearchResultsPage = lazy(() => import('@/pages/SearchResultsPage.jsx'));
const PaymentSuccessPage = lazy(() => import('@/pages/PaymentSuccessPage.jsx'));
const PaymentFailurePage = lazy(() => import('@/pages/PaymentFailurePage.jsx'));
const PaymentPendingPage = lazy(() => import('@/pages/PaymentPendingPage.jsx'));
const AboutPage = lazy(() => import('@/pages/AboutPage.jsx'));
const AccountPage = lazy(() => import('@/pages/AccountPage.jsx'));
const ContactPage = lazy(() => import('@/pages/ContactPage.jsx'));
const ForgotPasswordPage = lazy(() => import('@/pages/ForgotPasswordPage.jsx'));
const CatalogPage = lazy(() => import('@/pages/CatalogPage.jsx'));
const ResetPasswordPage = lazy(() => import('@/pages/ResetPasswordPage.jsx'));

// --- Layout y Páginas de Admin ---
const AdminLayout = lazy(() => import('@/pages/AdminLayout.jsx'));
const AdminDashboardPage = lazy(() => import('@/pages/AdminDashboardPage.jsx'));
const AdminProductsPage = lazy(() => import('@/pages/AdminProductsPage.jsx'));
const AdminProductFormPage = lazy(() => import('@/pages/AdminProductFormPage.jsx'));
const AdminProductVariantsPage = lazy(() => import('@/pages/AdminProductVariantsPage.jsx'));
const AdminOrdersPage = lazy(() => import('@/pages/AdminOrdersPage.jsx'));
const AdminOrderDetailPage = lazy(() => import('@/pages/AdminOrderDetailPage.jsx'));
const AdminUsersPage = lazy(() => import('@/pages/AdminUsersPage.jsx'));


const AppContent = () => {
  const location = useLocation();
  const isAdminRoute = location.pathname.startsWith('/admin');

  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const logoRef = useRef(null);
  const [logoPosition, setLogoPosition] = useState(null);
  const [isCartNotificationOpen, setIsCartNotificationOpen] = useState(false);
  const [addedItem, setAddedItem] = useState(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const { isAuthLoading, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // --- ¡ACÁ ESTÁ LA SOLUCIÓN A PRUEBA DE F5! ---
  useEffect(() => {
    if (isAdminRoute) {
      setLogoPosition(null);
      return;
    }

    const updatePosition = () => {
      if (logoRef.current) {
        const rect = logoRef.current.getBoundingClientRect();
        // Solo guardamos la posición si el logo es visible
        if (rect.width > 0 && rect.height > 0) {
          setLogoPosition(rect);
        }
      }
    };

    // Usamos un timeout para darle tiempo al navegador de renderizar todo después de un F5
    const timer = setTimeout(updatePosition, 100);

    window.addEventListener('resize', updatePosition);
    window.addEventListener('scroll', updatePosition);

    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', updatePosition);
      window.removeEventListener('scroll', updatePosition);
    };
  }, [isAdminRoute, location.pathname]); // Lo ejecutamos cada vez que cambia la ruta


  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
  const handleSetAddedItem = (item) => setAddedItem(item);
  const handleOpenSearch = () => setIsSearchOpen(true);
  const handleCloseSearch = () => setIsSearchOpen(false);
  const handleOpenCartNotification = () => setIsCartNotificationOpen(true);
  const handleCloseCartNotification = () => setIsCartNotificationOpen(false);

  useEffect(() => {
    let guestId = localStorage.getItem('guestSessionId');
    if (!guestId) {
      guestId = uuidv4();
      localStorage.setItem('guestSessionId', guestId);
    }
  }, []);

  useEffect(() => {
    setIsMenuOpen(false);
    setIsCartNotificationOpen(false);
    setIsSearchOpen(false);
    document.body.classList.remove('menu-open');
  }, [location]);

  useEffect(() => {
    if (isAdminRoute) return;
    document.body.classList.toggle('menu-open', isMenuOpen || isCartNotificationOpen || isSearchOpen);
  }, [isAdminRoute, isMenuOpen, isCartNotificationOpen, isSearchOpen]);

  if (isAuthLoading) {
    return <Spinner message="Verificando sesión..." />;
  }

  return (
    <div className="page-wrapper">
      <Navbar
        isMenuOpen={isMenuOpen}
        onToggleMenu={toggleMenu}
        onOpenSearch={handleOpenSearch}
        ref={logoRef}
      />
      <Suspense fallback={<Spinner message="Cargando página..." />}>
        <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/shop" element={<CatalogPage />} />
            <Route path="/catalog/:categoryName" element={<CatalogPage />} />
            <Route
                path="/product/:productId"
                element={<ProductPage
                onOpenCartModal={handleOpenCartNotification}
                onSetAddedItem={handleSetAddedItem}
                />}
            />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/cart" element={<CartPage />} />
            <Route path="/checkout" element={<ProtectedRoute><CheckoutPage /></ProtectedRoute>} />
            <Route path="/search" element={<SearchResultsPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/account" element={<ProtectedRoute><AccountPage /></ProtectedRoute>} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
            <Route path="/payment/success" element={<PaymentSuccessPage />} />
            <Route path="/payment/failure" element={<PaymentFailurePage />} />
            <Route path="/payment/pending" element={<PaymentPendingPage />} />

            <Route path="/admin/*" element={<AdminLayout />}>
                <Route index element={<AdminDashboardPage />} />
                <Route path="products" element={<AdminProductsPage />} />
                <Route path="products/new" element={<AdminProductFormPage />} />
                <Route path="products/edit/:productId" element={<AdminProductFormPage />} />
                <Route path="products/:productId/variants" element={<AdminProductVariantsPage />} />
                <Route path="users" element={<AdminUsersPage />} />
                <Route path="orders" element={<AdminOrdersPage />} />
                <Route path="orders/:orderId" element={<AdminOrderDetailPage />} />
            </Route>
        </Routes>
      </Suspense>
      
      {!isAdminRoute && (
        <>
            <Footer />
            <DropdownMenu 
                isOpen={isMenuOpen} 
                onClose={() => setIsMenuOpen(false)} 
                logoPosition={logoPosition}
                onOpenSearch={handleOpenSearch}
            />
            <SearchModal isOpen={isSearchOpen} onClose={handleCloseSearch} />
            <Chatbot />
        </>
      )}
      
      {isCartNotificationOpen && <CartNotificationModal item={addedItem} onClose={handleCloseCartNotification} />}
    </div>
  );
};

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;