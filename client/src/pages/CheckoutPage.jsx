// client/src/pages/CheckoutPage.jsx

import React, { useState, useEffect, useContext, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { CartContext } from '../context/CartContext';
import { NotificationContext } from '../context/NotificationContext';
import { createCheckoutPreference } from '../api/checkoutApi';
import { getLastAddressAPI } from '../api/userApi';
import { useAuthStore } from '../stores/useAuthStore';
import Spinner from '../components/common/Spinner';

const CheckoutPage = () => {
    const { t } = useTranslation();
    const [formData, setFormData] = useState({
        firstName: '', lastName: '', streetAddress: '', comments: '',
        city: '', postalCode: '', country: 'Argentina', state: '', phone: ''
    });
    const [shippingMethod, setShippingMethod] = useState('express');
    const [paymentMethod, setPaymentMethod] = useState('mercadoPago');
    const [isProcessing, setIsProcessing] = useState(false);
    
    const { cart, loading: cartLoading } = useContext(CartContext);
    const { notify } = useContext(NotificationContext);
    const { isAuthenticated } = useAuthStore();
    const navigate = useNavigate();

    useEffect(() => {
        const fetchLastAddress = async () => {
            if (isAuthenticated) {
                try {
                    const lastAddress = await getLastAddressAPI();
                    if (lastAddress) {
                        setFormData(prev => ({ ...prev, ...lastAddress }));
                        notify(t('checkout_info_address_loaded'), 'success');
                    }
                } catch (error) {
                    console.log('No previous address found or error fetching it.');
                }
            }
        };
        fetchLastAddress();
    }, [isAuthenticated, notify, t]);

    const isFormValid = useMemo(() => {
        const requiredFields = ['firstName', 'lastName', 'streetAddress', 'city', 'postalCode', 'country', 'state', 'phone'];
        return requiredFields.every(field => formData[field] && formData[field].trim() !== '');
    }, [formData]);

    const subtotal = cart?.items.reduce((sum, item) => sum + item.quantity * item.price, 0) || 0;
    const shippingCost = shippingMethod === 'express' ? 8000 : 0;
    const total = subtotal + shippingCost;

    const handleFormChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handlePlaceOrder = async (e) => {
        e.preventDefault();
        
        if (!isFormValid) {
            notify(t('checkout_error_fields'), 'error');
            return;
        }
        setIsProcessing(true);

        if (!cart || cart.items.length === 0) {
            notify(t('checkout_error_empty_cart'), 'error');
            setIsProcessing(false);
            return;
        }

        if (paymentMethod === 'mercadoPago') {
            try {
                // --- ¡ACÁ ESTÁ LA MAGIA DEL FRONTEND! ---
                // Ahora le pasamos el `shippingCost` a la función de la API
                const preference = await createCheckoutPreference(cart, formData, shippingCost);
                if (preference.init_point) {
                    // Abrir Mercado Pago en una nueva ventana/pestaña
                    const width = 800;
                    const height = 700;
                    const left = (window.innerWidth - width) / 2;
                    const top = (window.innerHeight - height) / 2;
                    
                    const mercadoPagoWindow = window.open(
                        preference.init_point,
                        'MercadoPago',
                        `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
                    );
                    
                    if (!mercadoPagoWindow) {
                        // Si el navegador bloqueó la ventana emergente, usar el método tradicional
                        notify(t('checkout_popup_blocked'), 'warning');
                        window.open(preference.init_point, '_blank');
                    } else {
                        notify(t('checkout_redirecting_to_payment'), 'success');
                        
                        // Opcional: Detectar cuando se cierra la ventana de pago
                        const checkWindowClosed = setInterval(() => {
                            if (mercadoPagoWindow.closed) {
                                clearInterval(checkWindowClosed);
                                console.log('Ventana de Mercado Pago cerrada');
                                // Aquí podrías verificar el estado del pago
                            }
                        }, 1000);
                    }
                } else {
                    throw new Error('Could not retrieve payment starting point.');
                }
            } catch (error) {
                console.error('Error creating payment preference:', error);
                notify(error.message || t('checkout_error_payment'), 'error');
                setIsProcessing(false);
            }
        }
    };

    const formatPrice = (price) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency', currency: 'ARS',
            minimumFractionDigits: 0, maximumFractionDigits: 0,
        }).format(price).replace("ARS", "$").trim();
    };

    if (cartLoading) return <div className="checkout-page-container"><Spinner message={t('checkout_loading')} /></div>;

    // El resto del JSX para renderizar el formulario queda exactamente igual
    return (
        <main className="checkout-page-container">
            <h1 className="checkout-title">{t('checkout_title')}</h1>
            <div className="checkout-content">
                <form id="checkout-form" onSubmit={handlePlaceOrder} className="checkout-form-section">
                    <h2 className="section-title">{t('checkout_shipping_address')}</h2>
                    <div className="form-grid">
                         <div className="input-group">
                            <label htmlFor="firstName">{t('checkout_first_name')}</label>
                            <input type="text" id="firstName" name="firstName" value={formData.firstName} onChange={handleFormChange} required />
                        </div>
                        <div className="input-group">
                            <label htmlFor="lastName">{t('checkout_last_name')}</label>
                            <input type="text" id="lastName" name="lastName" value={formData.lastName} onChange={handleFormChange} required />
                        </div>
                        <div className="input-group full-width">
                            <label htmlFor="streetAddress">{t('checkout_street_address')}</label>
                            <input type="text" id="streetAddress" name="streetAddress" value={formData.streetAddress} onChange={handleFormChange} required />
                        </div>
                        <div className="input-group">
                            <label htmlFor="comments">{t('checkout_comments_optional')}</label>
                            <input type="text" id="comments" name="comments" value={formData.comments} onChange={handleFormChange} />
                        </div>
                        <div className="input-group">
                            <label htmlFor="city">{t('checkout_city')}</label>
                            <input type="text" id="city" name="city" value={formData.city} onChange={handleFormChange} required />
                        </div>
                        <div className="input-group">
                            <label htmlFor="postalCode">{t('checkout_postal_code')}</label>
                            <input type="text" id="postalCode" name="postalCode" value={formData.postalCode} onChange={handleFormChange} required />
                        </div>
                        <div className="input-group">
                            <label htmlFor="country">{t('checkout_country')}</label>
                            <input type="text" id="country" name="country" value={formData.country} onChange={handleFormChange} required />
                        </div>
                        <div className="input-group">
                            <label htmlFor="state">{t('checkout_state')}</label>
                            <input type="text" id="state" name="state" value={formData.state} onChange={handleFormChange} required />
                        </div>
                        <div className="input-group">
                            <label htmlFor="prefix">{t('checkout_prefix')}</label>
                            <input type="text" id="prefix" name="prefix" value={formData.prefix} onChange={handleFormChange} />
                        </div>
                        <div className="input-group">
                            <label htmlFor="phone">{t('checkout_phone')}</label>
                            <input type="text" id="phone" name="phone" value={formData.phone} onChange={handleFormChange} required />
                        </div>
                    </div>
                    <h2 className="section-title mt-8">{t('checkout_shipping_method')}</h2>
                    <div className="shipping-options">
                        <div className="radio-option">
                           <span>{formatPrice(shippingCost)} ARS</span> {t('checkout_shipping_express')}
                           <p className="description">{t('checkout_shipping_express_desc')}</p>
                        </div>
                    </div>
                    <h2 className="section-title mt-8">{t('checkout_payment_method')}</h2>
                    <div className="payment-options">
                        <div className="radio-option">
                            <p>{t('checkout_payment_mp')}</p>
                        </div>
                    </div>
                </form>
                <aside className="order-summary-section">
                    <h2 className="section-title">{t('checkout_order_summary')}</h2>
                    <div className="order-summary-items">
                        {cart?.items.map(item => (
                            <div className="order-item" key={item.variante_id}>
                                <img src={item.image_url || '/img/placeholder.jpg'} alt={item.name} className="order-item-image"/>
                                <div className="order-item-details">
                                    <p className="item-name">{item.name}</p>
                                    <p className="item-size">SIZE: {item.size}</p>
                                </div>
                                <span className="item-price">{formatPrice(item.price)} ARS</span>
                            </div>
                        ))}
                    </div>
                    <div className="summary-line">
                        <span>{t('checkout_subtotal')}</span>
                        <span>{formatPrice(subtotal)} ARS</span>
                    </div>
                    <div className="summary-line">
                        <span>{t('checkout_shipping')}</span>
                        <span>{formatPrice(shippingCost)} ARS</span>
                    </div>
                    <div className="summary-line total">
                        <span>{t('checkout_total')}</span>
                        <span>{formatPrice(total)} ARS</span>
                    </div>
                    <button 
                        type="submit" 
                        form="checkout-form" 
                        className="place-order-button" 
                        disabled={isProcessing || !isFormValid}
                    >
                        {isProcessing ? t('checkout_processing_button') : t('checkout_place_order_button')}
                    </button>
                </aside>
            </div>
        </main>
    );
};

export default CheckoutPage;