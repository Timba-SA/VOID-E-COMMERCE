// En FRONTEND/src/components/products/CartNotificationModal.jsx
import React from 'react';
import { Link } from 'react-router-dom';

const CartNotificationModal = ({ item, onClose }) => {
    if (!item) return null;

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
        <div className="cart-notification-overlay" onClick={onClose}>
            <div className="cart-notification-modal" onClick={(e) => e.stopPropagation()}>
                <button onClick={onClose} className="cart-notification-close-btn">
                    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M1 1L17 17M17 1L1 17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                    </svg>
                </button>
                
                <div className="cart-notification-header">
                    <h3>ITEM ADDED TO BAG</h3>
                </div>

                <div className="cart-notification-item">
                    <div className="cart-notification-image">
                        <img src={item.image_url} alt={item.name} />
                    </div>
                    <div className="cart-notification-details">
                        <p>VOID</p>
                        <p>{item.name}</p>
                        <p>SIZE: {item.size}</p>
                    </div>
                    <p className="cart-notification-price">{formatPrice(item.price)} ARS</p>
                </div>

                <div className="cart-notification-summary">
                    <div className="summary-line">
                        <span>SUBTOTAL</span>
                        <span>{formatPrice(subtotal)} ARS</span>
                    </div>
                    <div className="summary-line">
                        <span>SHIPPING ESTIMATE</span>
                        <span className="summary-info">CALCULATED AT CHECKOUT</span>
                    </div>
                    <div className="summary-line total-line">
                        <span>ORDER TOTAL</span>
                        <span>{formatPrice(subtotal)} ARS</span>
                    </div>
                </div>

                <div className="cart-notification-actions">
                    <Link to="/cart" className="action-button secondary-button" onClick={onClose}>
                        VIEW BAG
                    </Link>
                    <button onClick={onClose} className="action-button primary-button">
                        CONTINUE SHOPPING
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CartNotificationModal;