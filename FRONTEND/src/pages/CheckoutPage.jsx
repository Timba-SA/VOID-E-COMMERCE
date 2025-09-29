import React, { useState, useEffect, useContext, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { CartContext } from '../context/CartContext';
import { NotificationContext } from '../context/NotificationContext';
import { createCheckoutPreference } from '../api/checkoutApi';
import { getLastAddressAPI } from '../api/userApi';
import { useAuthStore } from '../stores/useAuthStore';
import Spinner from '../components/common/Spinner';

const CheckoutPage = () => {
    const [formData, setFormData] = useState({
        firstName: '',
        lastName: '',
        streetAddress: '',
        comments: '',
        city: '',
        postalCode: '',
        country: 'Argentina',
        state: '',
        prefix: '+54',
        phone: ''
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
                        notify('Previous address loaded.', 'success');
                    }
                } catch (error) {
                    console.log('No previous address found or error fetching it.');
                }
            }
        };
        fetchLastAddress();
    }, [isAuthenticated, notify]);

    const isFormValid = useMemo(() => {
        const requiredFields = ['firstName', 'lastName', 'streetAddress', 'city', 'postalCode', 'country', 'state', 'phone'];
        return requiredFields.every(field => formData[field] && formData[field].trim() !== '');
    }, [formData]);

    const subtotal = cart?.items.reduce((sum, item) => sum + item.quantity * item.price, 0) || 0;
    const shippingCost = shippingMethod === 'express' ? 8000 : 0; // Ejemplo de costo de envío
    const total = subtotal + shippingCost;

    const handleFormChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handlePlaceOrder = async (e) => {
        e.preventDefault();
        
        if (!isFormValid) {
            notify('Please complete all required shipping address fields.', 'error');
            return;
        }

        setIsProcessing(true);

        if (!cart || cart.items.length === 0) {
            notify('Your cart is empty.', 'error');
            setIsProcessing(false);
            return;
        }

        if (paymentMethod === 'mercadoPago') {
            try {
                const preference = await createCheckoutPreference(cart, formData);
                if (preference.init_point) {
                    window.location.href = preference.init_point;
                } else {
                    throw new Error('Could not retrieve payment starting point.');
                }
            } catch (error) {
                console.error('Error creating payment preference:', error);
                notify(error.message || 'Could not initiate the payment process.', 'error');
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

    if (cartLoading) return <div className="checkout-page-container"><Spinner message="Loading checkout..." /></div>;

    return (
        <main className="checkout-page-container">
            <h1 className="checkout-title">CHECKOUT</h1>
            <div className="checkout-content">
                <form id="checkout-form" onSubmit={handlePlaceOrder} className="checkout-form-section">
                    <h2 className="section-title">SHIPPING ADDRESS</h2>
                    <div className="form-grid">
                         <div className="input-group">
                            <label htmlFor="firstName">FIRST NAME</label>
                            <input type="text" id="firstName" name="firstName" value={formData.firstName} onChange={handleFormChange} required />
                        </div>
                        <div className="input-group">
                            <label htmlFor="lastName">LAST NAME</label>
                            <input type="text" id="lastName" name="lastName" value={formData.lastName} onChange={handleFormChange} required />
                        </div>
                        <div className="input-group full-width">
                            <label htmlFor="streetAddress">STREET ADDRESS</label>
                            <input type="text" id="streetAddress" name="streetAddress" value={formData.streetAddress} onChange={handleFormChange} required />
                        </div>
                        <div className="input-group">
                            <label htmlFor="comments">COMMENTS (OPTIONAL)</label>
                            <input type="text" id="comments" name="comments" value={formData.comments} onChange={handleFormChange} />
                        </div>
                        <div className="input-group">
                            <label htmlFor="city">CITY</label>
                            <input type="text" id="city" name="city" value={formData.city} onChange={handleFormChange} required />
                        </div>
                        <div className="input-group">
                            <label htmlFor="postalCode">POSTAL CODE</label>
                            <input type="text" id="postalCode" name="postalCode" value={formData.postalCode} onChange={handleFormChange} required />
                        </div>
                        <div className="input-group">
                            <label htmlFor="country">COUNTRY</label>
                            <input type="text" id="country" name="country" value={formData.country} onChange={handleFormChange} required />
                        </div>
                        <div className="input-group">
                            <label htmlFor="state">STATE</label>
                            <input type="text" id="state" name="state" value={formData.state} onChange={handleFormChange} required />
                        </div>
                        <div className="input-group">
                            <label htmlFor="prefix">PREFIX</label>
                            <input type="text" id="prefix" name="prefix" value={formData.prefix} onChange={handleFormChange} />
                        </div>
                        <div className="input-group">
                            <label htmlFor="phone">PHONE</label>
                            <input type="text" id="phone" name="phone" value={formData.phone} onChange={handleFormChange} required />
                        </div>
                    </div>

                    <h2 className="section-title mt-8">SHIPPING METHOD</h2>
                    <div className="shipping-options">
                        <div className="radio-option">
                           <span>{formatPrice(shippingCost)} ARS</span> EXPRESS
                           <p className="description">DELIVERY BETWEEN 3 TO 5 BUSINESS DAY</p>
                        </div>
                    </div>


                    <h2 className="section-title mt-8">PAYMENT METHOD</h2>
                    <div className="payment-options">
                        <div className="radio-option">
                            <p>PAY WITH MERCADO PAGO</p>
                        </div>
                    </div>
                </form>

                <aside className="order-summary-section">
                    <h2 className="section-title">ORDER SUMMARY</h2>
                    
                    {/* --- ACÁ ESTABA EL PROBLEMA, FIERA --- */}
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
                    {/* --- FIN DEL ARREGLO --- */}

                    <div className="summary-line">
                        <span>SUBTOTAL</span>
                        <span>{formatPrice(subtotal)} ARS</span>
                    </div>
                    <div className="summary-line">
                        <span>SHIPPING</span>
                        <span>{formatPrice(shippingCost)} ARS</span>
                    </div>
                    <div className="summary-line total">
                        <span>TOTAL</span>
                        <span>{formatPrice(total)} ARS</span>
                    </div>

                    <button 
                        type="submit" 
                        form="checkout-form" 
                        className="place-order-button" 
                        disabled={isProcessing || !isFormValid}
                    >
                        {isProcessing ? 'PROCESSING...' : 'PLACE ORDER'}
                    </button>
                </aside>
            </div>
        </main>
    );
};

export default CheckoutPage;