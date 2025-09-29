// En FRONTEND/src/pages/CartPage.jsx

import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { CartContext } from '../context/CartContext';
import { useAuthStore } from '../stores/useAuthStore';
import Spinner from '../components/common/Spinner';

const CartPage = () => {
    const navigate = useNavigate();
    const { cart, loading, removeItemFromCart } = useContext(CartContext);
    const { isAuthenticated } = useAuthStore();

    const handleCheckout = () => {
        if (isAuthenticated) {
            navigate('/checkout');
        } else {
            navigate('/login', { state: { from: '/checkout' } });
        }
    };

    const formatPrice = (price) => {
        return new Intl.NumberFormat('es-AR', {
            style: 'currency',
            currency: 'ARS',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(price).replace("ARS", "$").trim();
    };

    if (loading) return <main className="cart-page-container"><Spinner message="Cargando carrito..." /></main>;

    const subtotal = cart?.items.reduce((sum, item) => sum + item.price * item.quantity, 0) || 0;
    const orderTotal = subtotal;

    return (
        <main className="cart-page-container">
            <h1 className="cart-page-title">SHOPPING BAG</h1>
            
            <div className="cart-content">
                <div className="cart-header">
                    <span>ITEM</span>
                    <button onClick={() => navigate(-1)} className="cart-close-btn">
                        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M1 1L17 17M17 1L1 17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                        </svg>
                    </button>
                </div>

                {(!cart?.items || cart.items.length === 0) ? (
                    <div className="cart-empty-message">
                        <p>Tu carrito está vacío.</p>
                    </div>
                ) : (
                    <>
                        <div className="cart-items-list">
                            {cart.items.map(item => (
                                <div className="cart-item-row" key={item.variante_id}>
                                    <div className="item-info-left">
                                        <div className="item-image">
                                            <img src={item.image_url || '/img/placeholder.jpg'} alt={item.name} />
                                        </div>
                                        <div className="item-details">
                                            <h3>VOID</h3>
                                            <p>{item.name}</p>
                                            <p>SIZE: {item.size}</p>
                                        </div>
                                    </div>
                                    <div className="item-info-right">
                                        <span className="item-price">{formatPrice(item.price * item.quantity)} ARS</span>
                                        <button 
                                            onClick={() => removeItemFromCart(item.variante_id)} 
                                            className="item-remove-btn"
                                        >
                                            REMOVE
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="cart-summary-section">
                            <div className="summary-line">
                                <span>SUBTOTAL</span>
                                <span>{formatPrice(subtotal)} ARS</span>
                            </div>
                            <div className="summary-line">
                                <span>SHIPPING ESTIMATE</span>
                                <span>CALCULATED AT CHECKOUT</span>
                            </div>
                            <div className="summary-line total">
                                <span>ORDER TOTAL</span>
                                <span>{formatPrice(orderTotal)} ARS</span>
                            </div>
                            <div className="checkout-button-container">
                                <button onClick={handleCheckout} className="checkout-button">CHECKOUT</button>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </main>
    );
};

export default CartPage;