// En FRONTEND/src/components/products/CartNotificationModal.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next'; // <-- 1. IMPORTAMOS LA MAGIA

const CartNotificationModal = ({ item, onClose }) => {
    const { t } = useTranslation(); // <-- 2. INICIALIZAMOS

    if (!item) {
        return null;
    }

    // --- ESTILOS "A LO BRUTO" PARA FORZAR QUE SE VEA ---
    const overlayStyles = {
        position: 'fixed',
        top: '0',
        left: '0',
        width: '100vw',
        height: '100vh',
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: '9999',
        opacity: '1'
    };

    const modalStyles = {
        backgroundColor: 'white',
        padding: '2rem',
        width: '90%',
        maxWidth: '480px',
        position: 'relative',
        opacity: '1',
        transform: 'scale(1)'
    };
    // --- FIN DE LOS ESTILOS "A LO BRUTO" ---

    const subtotal = item.price;

    const formatPrice = (price) => {
        return new Intl.NumberFormat('es-AR', {
          style: 'currency',
          currency: 'ARS',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(price).replace("ARS", "$").trim();
    };

    return (
        <div style={overlayStyles} onClick={onClose}>
            <div style={modalStyles} onClick={(e) => e.stopPropagation()}>
                <button onClick={onClose} className="cart-notification-close-btn">
                    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M1 1L17 17M17 1L1 17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                    </svg>
                </button>
                
                {/* --- 3. ACÁ EMPIEZAN LAS TRADUCCIONES --- */}
                <div className="cart-notification-header">
                    <h3>{t('modal_item_added_title')}</h3>
                </div>

                <div className="cart-notification-item">
                    <div className="cart-notification-image">
                        <img src={item.image_url || '/img/placeholder.jpg'} alt={item.name} />
                    </div>
                    <div className="cart-notification-details">
                        <p>VOID</p>
                        <p>{item.name}</p>
                        <p>{t('modal_size', { size: item.size })}</p>
                    </div>
                    <p className="cart-notification-price">{formatPrice(item.price)} ARS</p>
                </div>

                <div className="cart-notification-summary">
                    <div className="summary-line">
                        <span>{t('modal_subtotal')}</span>
                        <span>{formatPrice(subtotal)} ARS</span>
                    </div>
                    <div className="summary-line">
                        <span>{t('modal_shipping_estimate')}</span>
                        <span className="summary-info">{t('modal_calculated_at_checkout')}</span>
                    </div>
                    <div className="summary-line total-line">
                        <span>{t('modal_order_total')}</span>
                        <span>{formatPrice(subtotal)} ARS</span>
                    </div>
                </div>

                <div className="cart-notification-actions">
                    <Link to="/cart" className="action-button secondary-button" onClick={onClose}>
                        {t('modal_view_bag_button')}
                    </Link>
                    <button onClick={onClose} className="action-button primary-button">
                        {t('modal_continue_shopping_button')}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CartNotificationModal;