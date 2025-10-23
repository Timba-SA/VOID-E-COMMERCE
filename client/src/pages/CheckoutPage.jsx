// client/src/pages/CheckoutPage.jsx

import React, { useState, useEffect, useContext, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { CartContext } from '../context/CartContext';
import { NotificationContext } from '../context/NotificationContext';
import { createCheckoutPreference } from '../api/checkoutApi';
import { getAddressesAPI, addAddressAPI } from '../api/userApi';
import { getMyOrdersAPI } from '../api/ordersApi';
import { useAuthStore } from '../stores/useAuthStore';
import Spinner from '../components/common/Spinner';
import { countryPrefixes } from '../utils/countryPrefixes';

const CheckoutPage = () => {
    const { t } = useTranslation();
    const [savedAddresses, setSavedAddresses] = useState([]);
    const [selectedAddressId, setSelectedAddressId] = useState('new');
    const [formData, setFormData] = useState({
        firstName: '', lastName: '', streetAddress: '', comments: '',
        city: '', postalCode: '', country: 'Argentina', state: '', prefix: '+54', phone: ''
    });
    const [saveAddress, setSaveAddress] = useState(false);
    const [shippingMethod, setShippingMethod] = useState('express');
    const [paymentMethod, setPaymentMethod] = useState('mercadoPago');
    const [isProcessing, setIsProcessing] = useState(false);
    
    const { cart, loading: cartLoading } = useContext(CartContext);
    const { notify } = useContext(NotificationContext);
    const { isAuthenticated, user } = useAuthStore();
    const navigate = useNavigate();

    useEffect(() => {
        const fetchAddresses = async () => {
            if (isAuthenticated) {
                try {
                    const addresses = await getAddressesAPI();
                    setSavedAddresses(addresses);
                    
                    // Si hay direcciones, seleccionar la última por defecto
                    if (addresses.length > 0) {
                        const lastAddress = addresses[addresses.length - 1];
                        setSelectedAddressId(lastAddress.address_id);
                        setFormData({
                            firstName: lastAddress.firstName || '',
                            lastName: lastAddress.lastName || '',
                            streetAddress: lastAddress.streetAddress || '',
                            comments: lastAddress.comments || '',
                            city: lastAddress.city || '',
                            postalCode: lastAddress.postalCode || '',
                            country: lastAddress.country || 'Argentina',
                            state: lastAddress.state || '',
                            prefix: lastAddress.prefix || '',
                            phone: lastAddress.phone || ''
                        });
                    }
                } catch (error) {
                    console.log('No addresses found or error fetching them.');
                }
            }
        };
        fetchAddresses();
    }, [isAuthenticated]);

    const isFormValid = useMemo(() => {
        const requiredFields = ['firstName', 'lastName', 'streetAddress', 'city', 'postalCode', 'country', 'state', 'phone'];
        return requiredFields.every(field => formData[field] && formData[field].trim() !== '');
    }, [formData]);

    const subtotal = cart?.items.reduce((sum, item) => sum + item.quantity * item.price, 0) || 0;
    const shippingCost = shippingMethod === 'express' ? 8000 : 0;
    const total = subtotal + shippingCost;

    const handleAddressSelect = (e) => {
        const addressId = e.target.value;
        setSelectedAddressId(addressId);
        
        if (addressId === 'new') {
            // Limpiar el formulario para nueva dirección
            setFormData({
                firstName: '', lastName: '', streetAddress: '', comments: '',
                city: '', postalCode: '', country: 'Argentina', state: '', prefix: '+54', phone: ''
            });
        } else {
            // Cargar la dirección seleccionada
            const selectedAddress = savedAddresses.find(addr => addr.address_id === addressId);
            if (selectedAddress) {
                setFormData({
                    firstName: selectedAddress.firstName || '',
                    lastName: selectedAddress.lastName || '',
                    streetAddress: selectedAddress.streetAddress || '',
                    comments: selectedAddress.comments || '',
                    city: selectedAddress.city || '',
                    postalCode: selectedAddress.postalCode || '',
                    country: selectedAddress.country || 'Argentina',
                    state: selectedAddress.state || '',
                    prefix: selectedAddress.prefix || '',
                    phone: selectedAddress.phone || ''
                });
            }
        }
    };

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

        // Si es una dirección nueva y el usuario quiere guardarla
        if (selectedAddressId === 'new' && saveAddress && isAuthenticated) {
            try {
                await addAddressAPI(formData);
                console.log('✅ Dirección guardada para futuros pedidos');
            } catch (error) {
                console.error('❌ Error al guardar dirección:', error);
            }
        }

        if (paymentMethod === 'mercadoPago') {
            try {
                // Agregar el email del usuario al formData
                const addressWithEmail = {
                    ...formData,
                    email: user?.email || ''
                };
                
                // --- ¡ACÁ ESTÁ LA MAGIA DEL FRONTEND! ---
                // Ahora le pasamos el `shippingCost` a la función de la API
                const preference = await createCheckoutPreference(cart, addressWithEmail, shippingCost);
                if (preference.init_point) {
                    console.log('🚀 Intentando abrir Mercado Pago...');
                    
                    // Intentar abrir en la misma pestaña (siempre funciona)
                    // Guardar el estado actual para poder reanudar después
                    window.location.href = preference.init_point;
                    
                    // No hay que hacer polling ni nada más porque MP redirigirá de vuelta
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
                    
                    {/* Selector de direcciones guardadas */}
                    {isAuthenticated && savedAddresses.length > 0 && (
                        <div className="saved-addresses-selector">
                            <label htmlFor="addressSelect">{t('select_saved_address', 'Seleccionar dirección guardada')}</label>
                            <select 
                                id="addressSelect" 
                                value={selectedAddressId} 
                                onChange={handleAddressSelect}
                                className="address-select"
                            >
                                <option value="new">{t('use_new_address', '+ Usar nueva dirección')}</option>
                                {savedAddresses.map((addr) => (
                                    <option key={addr.address_id} value={addr.address_id}>
                                        {addr.firstName} {addr.lastName} - {addr.streetAddress}, {addr.city}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}
                    
                    <div className="form-grid">
                         <div className="input-group">
                            <label htmlFor="firstName">{t('checkout_first_name')}</label>
                            <input 
                                type="text" 
                                id="firstName" 
                                name="firstName" 
                                value={formData.firstName} 
                                onChange={handleFormChange} 
                                disabled={selectedAddressId !== 'new'}
                                required 
                            />
                        </div>
                        <div className="input-group">
                            <label htmlFor="lastName">{t('checkout_last_name')}</label>
                            <input 
                                type="text" 
                                id="lastName" 
                                name="lastName" 
                                value={formData.lastName} 
                                onChange={handleFormChange} 
                                disabled={selectedAddressId !== 'new'}
                                required 
                            />
                        </div>
                        <div className="input-group full-width">
                            <label htmlFor="streetAddress">{t('checkout_street_address')}</label>
                            <input 
                                type="text" 
                                id="streetAddress" 
                                name="streetAddress" 
                                value={formData.streetAddress} 
                                onChange={handleFormChange} 
                                disabled={selectedAddressId !== 'new'}
                                required 
                            />
                        </div>
                        <div className="input-group">
                            <label htmlFor="comments">{t('checkout_comments_optional')}</label>
                            <input 
                                type="text" 
                                id="comments" 
                                name="comments" 
                                value={formData.comments} 
                                onChange={handleFormChange} 
                                disabled={selectedAddressId !== 'new'}
                            />
                        </div>
                        <div className="input-group">
                            <label htmlFor="city">{t('checkout_city')}</label>
                            <input 
                                type="text" 
                                id="city" 
                                name="city" 
                                value={formData.city} 
                                onChange={handleFormChange} 
                                disabled={selectedAddressId !== 'new'}
                                required 
                            />
                        </div>
                        <div className="input-group">
                            <label htmlFor="postalCode">{t('checkout_postal_code')}</label>
                            <input 
                                type="text" 
                                id="postalCode" 
                                name="postalCode" 
                                value={formData.postalCode} 
                                onChange={handleFormChange} 
                                disabled={selectedAddressId !== 'new'}
                                required 
                            />
                        </div>
                        <div className="input-group">
                            <label htmlFor="country">{t('checkout_country')}</label>
                            <input 
                                type="text" 
                                id="country" 
                                name="country" 
                                value={formData.country} 
                                onChange={handleFormChange} 
                                disabled={selectedAddressId !== 'new'}
                                required 
                            />
                        </div>
                        <div className="input-group">
                            <label htmlFor="state">{t('checkout_state')}</label>
                            <input 
                                type="text" 
                                id="state" 
                                name="state" 
                                value={formData.state} 
                                onChange={handleFormChange} 
                                disabled={selectedAddressId !== 'new'}
                                required 
                            />
                        </div>
                        
                        {/* Campo de teléfono con prefijo y número separados */}
                        <div className="input-group">
                            <label htmlFor="phone">{t('checkout_phone')}</label>
                            <div className="phone-input-wrapper">
                                <select
                                    id="prefix"
                                    name="prefix"
                                    value={formData.prefix}
                                    onChange={handleFormChange}
                                    disabled={selectedAddressId !== 'new'}
                                    required
                                    className="phone-prefix-select"
                                >
                                    {countryPrefixes.map(country => (
                                        <option key={country.code} value={country.code}>
                                            {country.code} {country.iso}
                                        </option>
                                    ))}
                                </select>
                                <input 
                                    type="tel" 
                                    id="phone" 
                                    name="phone" 
                                    value={formData.phone} 
                                    onChange={handleFormChange}
                                    placeholder="2611111111"
                                    disabled={selectedAddressId !== 'new'}
                                    required
                                    className="phone-number-input"
                                />
                            </div>
                        </div>
                    </div>
                    
                    {/* Checkbox para guardar nueva dirección */}
                    {isAuthenticated && selectedAddressId === 'new' && (
                        <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <input 
                                type="checkbox" 
                                id="saveAddress" 
                                checked={saveAddress}
                                onChange={(e) => setSaveAddress(e.target.checked)}
                                style={{ cursor: 'pointer' }}
                            />
                            <label htmlFor="saveAddress" style={{ cursor: 'pointer', fontSize: '0.9rem' }}>
                                {t('save_address_for_future', 'Guardar esta dirección para futuros pedidos')}
                            </label>
                        </div>
                    )}
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