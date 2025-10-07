// En client/src/pages/CartPage.jsx
import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next'; // <-- 1. IMPORTAMOS LA MAGIA
import { CartContext } from '../context/CartContext';
import { useAuthStore } from '../stores/useAuthStore';
import Spinner from '../components/common/Spinner';

const CartPage = () => {
    const navigate = useNavigate();
    const { t } = useTranslation(); // <-- 2. INICIALIZAMOS EL TRADUCTOR
    const { cart, loading, removeItemFromCart, updateItemQuantity } = useContext(CartContext);
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
            {/* --- 3. ACÁ EMPIEZAN LOS CAMBIOS --- */}
            <h1 className="cart-page-title">{t('cart_title')}</h1>
            
            <div className="cart-content">
                <div className="cart-header">
                    <span>{t('cart_item')}</span>
                    <button onClick={() => navigate('/')} className="cart-close-btn">
                        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M1 1L17 17M17 1L1 17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                        </svg>
                    </button>
                </div>

                {(!cart?.items || cart.items.length === 0) ? (
                    <div className="cart-empty-message">
                        <p>{t('cart_empty')}</p>
                    </div>
                ) : (
                    <>
                        <div className="cart-items-list">
                            {cart.items.map(item => (
                                <div className="cart-item-row" key={item.variante_id}>
                                    <div className="item-image">
                                        <img src={item.image_url || '/img/placeholder.jpg'} alt={item.name} />
                                    </div>
                                    <div className="item-details">
                                        <h3>VOID</h3>
                                        <p>{item.name}</p>
                                        <p>{t('cart_size', { size: item.size })}</p>
                                    </div>
                                    
                                    {/* ========= ¡ACÁ ESTÁ EL CAMBIO, PAPÁ! ========= */}
                                    <div className="item-actions">
                                        <div className="quantity-selector">
                                            <button 
                                                className="quantity-btn" 
                                                onClick={() => updateItemQuantity(item.variante_id, item.quantity - 1)}
                                            >
                                                -
                                            </button>
                                            <span className="quantity-display">{item.quantity}</span>
                                            <button 
                                                className="quantity-btn" 
                                                onClick={() => updateItemQuantity(item.variante_id, item.quantity + 1)}
                                            >
                                                +
                                            </button>
                                        </div>
                                        <span className="item-price">{formatPrice(item.price * item.quantity)} ARS</span>
                                        <button 
                                            onClick={() => removeItemFromCart(item.variante_id)} 
                                            className="item-remove-btn"
                                        >
                                            {t('cart_remove')}
                                        </button>
                                    </div>
                                    {/* ========= FIN DEL CAMBIO ========= */}

                                </div>
                            ))}
                        </div>

                        <div className="cart-summary-section">
                            <div className="summary-line">
                                <span>{t('cart_subtotal')}</span>
                                <span>{formatPrice(subtotal)} ARS</span>
                            </div>
                            <div className="summary-line">
                                <span>{t('cart_shipping_estimate')}</span>
                                <span className="summary-info">{t('cart_calculated_at_checkout')}</span>
                            </div>
                            <div className="summary-line total">
                                <span>{t('cart_order_total')}</span>
                                <span>{formatPrice(orderTotal)} ARS</span>
                            </div>
                            <div className="checkout-button-container">
                                <button onClick={handleCheckout} className="checkout-button">{t('cart_checkout_button')}</button>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </main>
    );
};

export default CartPage;