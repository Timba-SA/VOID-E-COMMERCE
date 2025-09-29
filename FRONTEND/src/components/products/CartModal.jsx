// En FRONTEND/src/components/products/CartModal.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { useCart } from '../../hooks/useCart';

const CartModal = ({ isOpen, onClose }) => {
    const { cart, isLoading, error, removeItem } = useCart();
    
    // El modal ahora está "consciente" de su estado de apertura
    // y solo se renderiza si isOpen es true.
    const overlayClass = isOpen ? "cart-modal-overlay open" : "cart-modal-overlay";

    // --- MANEJO DE ESTADOS DE CARGA Y ERROR ---
    const renderContent = () => {
        if (isLoading) {
            return <p className="empty-cart-message">Cargando carrito...</p>;
        }
        if (error) {
            return <p className="empty-cart-message">Error al cargar el carrito.</p>;
        }
        if (!cart || cart.items.length === 0) {
            return <p className="empty-cart-message">Tu carrito está vacío.</p>;
        }

        const subtotal = cart.items.reduce((sum, item) => sum + item.price * item.quantity, 0) || 0;
        const orderTotal = subtotal;

        const formatPrice = (price) => {
            return new Intl.NumberFormat('es-AR', {
                style: 'currency',
                currency: 'ARS',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
            }).format(price).replace("ARS", "$").trim();
        };

        return (
            <>
                <div className="cart-items-list">
                    {cart.items.map(item => (
                        <div className="cart-item" key={item.variante_id}>
                            <div className="cart-item-image">
                                <img src={item.image_url || '/img/placeholder.jpg'} alt={item.name} />
                            </div>
                            <div className="cart-item-details">
                                <h3>VOID</h3>
                                <p>{item.name}</p>
                                <p>SIZE: {item.size}</p>
                            </div>
                            <div className="cart-item-info">
                                <span className="cart-item-price">{formatPrice(item.price * item.quantity)} ARS</span>
                                <button onClick={() => removeItem(item.variante_id)} className="cart-item-remove-btn">REMOVE</button>
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
                </div>
                
                <div className="cart-buttons-section">
                    <Link to="/cart" className="cart-button-link view-bag" onClick={onClose}>VIEW BAG</Link>
                    <Link to="/checkout" className="cart-button-link checkout" onClick={onClose}>CHECKOUT</Link>
                </div>
            </>
        );
    };

    return (
        <div className={overlayClass} onClick={onClose}>
            <div className="cart-modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="cart-modal-header">
                    <h2>SHOPPING BAG</h2>
                    <button onClick={onClose} className="cart-modal-close-btn">
                        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M1 1L17 17M17 1L1 17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                        </svg>
                    </button>
                </div>
                {renderContent()}
            </div>
        </div>
    );
};

export default CartModal;