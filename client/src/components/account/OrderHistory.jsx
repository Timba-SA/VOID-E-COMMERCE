import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { getOrderDetailsAPI } from '../../api/ordersApi';
import Spinner from '../common/Spinner';

const OrderHistory = ({ orders, loading }) => {
    const { t } = useTranslation();
    const [expandedOrderId, setExpandedOrderId] = useState(null);
    const [orderDetails, setOrderDetails] = useState({});
    const [loadingDetails, setLoadingDetails] = useState({});

    const formatPrice = (price) => {
        return new Intl.NumberFormat('es-AR', {
            minimumFractionDigits: 0, 
            maximumFractionDigits: 0,
        }).format(price);
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-AR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getStatusColor = (status) => {
        const statusMap = {
            'approved': 'success',
            'aprobado': 'success',
            'pending': 'warning',
            'pendiente': 'warning',
            'rejected': 'danger',
            'rechazado': 'danger',
            'cancelled': 'danger',
            'cancelado': 'danger'
        };
        return statusMap[status?.toLowerCase()] || 'default';
    };

    const translateStatus = (status) => {
        const statusTranslations = {
            'approved': 'Aprobado',
            'aprobado': 'Aprobado',
            'pending': 'Pendiente',
            'pendiente': 'Pendiente',
            'rejected': 'Rechazado',
            'rechazado': 'Rechazado',
            'cancelled': 'Cancelado',
            'cancelado': 'Cancelado'
        };
        return statusTranslations[status?.toLowerCase()] || status || 'N/A';
    };

    const handleViewDetails = async (orderId) => {
        console.log('Clicking order details for:', orderId);
        
        // Si ya está expandida, colapsarla
        if (expandedOrderId === orderId) {
            setExpandedOrderId(null);
            return;
        }

        // Si ya tenemos los detalles cacheados, solo expandir
        if (orderDetails[orderId]) {
            console.log('Using cached details');
            setExpandedOrderId(orderId);
            return;
        }

        // Cargar los detalles desde el backend
        console.log('Fetching details from API...');
        setLoadingDetails(prev => ({ ...prev, [orderId]: true }));
        try {
            const details = await getOrderDetailsAPI(orderId);
            console.log('Details received:', details);
            console.log('Direccion de envio:', details.direccion_envio);
            setOrderDetails(prev => ({ ...prev, [orderId]: details }));
            setExpandedOrderId(orderId);
        } catch (error) {
            console.error('Error loading order details:', error);
            alert('Error al cargar los detalles de la orden');
        } finally {
            setLoadingDetails(prev => ({ ...prev, [orderId]: false }));
        }
    };

    if (loading) {
        return <Spinner message="Cargando historial..." />;
    }

    if (!orders || orders.length === 0) {
        return (
            <div className="no-orders-container">
                <div className="no-orders-content">
                    <h3>Sin órdenes</h3>
                    <p>Cuando realices tu primera compra, aparecerá aquí.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="order-history-container">
            <h2 className="order-history-title">Historial de Compras</h2>
            
            <div className="orders-list">
                {orders.map(order => {
                    const isExpanded = expandedOrderId === order.id;
                    const details = orderDetails[order.id];
                    const isLoadingDetails = loadingDetails[order.id];

                    return (
                        <div key={order.id} className={`order-card ${isExpanded ? 'expanded' : ''}`}>
                            {/* Header de la orden */}
                            <div className="order-header">
                                <div className="order-header-main">
                                    <div className="order-id">
                                        <span className="order-label">ORDEN</span>
                                        <span className="order-number">#{order.id}</span>
                                    </div>
                                    <div className="order-date">
                                        {formatDate(order.creado_en)}
                                    </div>
                                </div>
                                
                                <div className="order-header-side">
                                    <div className="order-total">
                                        <span className="total-label">Total</span>
                                        <span className="total-amount">${formatPrice(order.monto_total)}</span>
                                    </div>
                                    <span className={`order-status status-${getStatusColor(order.estado_pago)}`}>
                                        {translateStatus(order.estado_pago)}
                                    </span>
                                </div>
                            </div>

                            {/* Info rápida */}
                            <div className="order-meta">
                                <span className="meta-item">
                                    <strong>{order.detalles?.length || 0}</strong> {order.detalles?.length === 1 ? 'producto' : 'productos'}
                                </span>
                                <span className="meta-divider">•</span>
                                <span className="meta-item">{order.metodo_pago || 'N/A'}</span>
                            </div>

                            {/* Botón de detalles */}
                            <button 
                                className="details-toggle-btn"
                                onClick={() => handleViewDetails(order.id)}
                                disabled={isLoadingDetails}
                            >
                                {isLoadingDetails ? (
                                    <>
                                        <span className="btn-spinner"></span>
                                        <span>Cargando...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>{isExpanded ? 'Ocultar detalles' : 'Ver detalles'}</span>
                                        <svg 
                                            className={`chevron-icon ${isExpanded ? 'rotated' : ''}`} 
                                            width="16" 
                                            height="16" 
                                            viewBox="0 0 16 16" 
                                            fill="none"
                                        >
                                            <path d="M4 6L8 10L12 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                        </svg>
                                    </>
                                )}
                            </button>

                            {/* Detalles expandidos */}
                            {isExpanded && details && (
                                <div className="order-details-panel">
                                    {/* Productos */}
                                    <div className="details-section">
                                        <h4 className="section-title">Productos</h4>
                                        <div className="products-grid">
                                            {details.detalles.map((item, index) => (
                                                <div key={index} className="product-row">
                                                    <div className="product-info">
                                                        <div className="product-name">
                                                            {item.variante_producto?.producto_nombre || 'Producto'}
                                                        </div>
                                                        <div className="product-variants">
                                                            <span className="variant-tag">
                                                                {item.variante_producto?.tamanio}
                                                            </span>
                                                            <span className="variant-tag">
                                                                {item.variante_producto?.color}
                                                            </span>
                                                        </div>
                                                    </div>
                                                    <div className="product-pricing">
                                                        <div className="price-detail">
                                                            <span className="price-label">Precio unitario</span>
                                                            <span className="price-value">${formatPrice(item.precio_en_momento_compra)}</span>
                                                        </div>
                                                        <div className="price-detail">
                                                            <span className="price-label">Cantidad</span>
                                                            <span className="price-value">×{item.cantidad}</span>
                                                        </div>
                                                        <div className="price-detail subtotal">
                                                            <span className="price-label">Subtotal</span>
                                                            <span className="price-value">${formatPrice(item.cantidad * item.precio_en_momento_compra)}</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Dirección de envío */}
                                    <div className="details-section">
                                        <h4 className="section-title">Dirección de Envío</h4>
                                        {details.direccion_envio ? (
                                            <div className="address-box">
                                                <p className="address-name">
                                                    {details.direccion_envio.firstName} {details.direccion_envio.lastName}
                                                </p>
                                                <p>{details.direccion_envio.streetAddress}</p>
                                                {details.direccion_envio.comments && (
                                                    <p className="address-note">{details.direccion_envio.comments}</p>
                                                )}
                                                <p>
                                                    {details.direccion_envio.city}, {details.direccion_envio.state} ({details.direccion_envio.postalCode})
                                                </p>
                                                <p>{details.direccion_envio.country}</p>
                                                <p className="address-phone">
                                                    {details.direccion_envio.prefix && `${details.direccion_envio.prefix.startsWith('+') ? details.direccion_envio.prefix : '+' + details.direccion_envio.prefix} `}
                                                    {details.direccion_envio.phone}
                                                </p>
                                            </div>
                                        ) : (
                                            <div className="address-box">
                                                <p style={{ color: '#737373', fontStyle: 'italic' }}>
                                                    No hay información de dirección registrada para esta orden.
                                                </p>
                                            </div>
                                        )}
                                    </div>

                                    {/* Resumen de pago */}
                                    <div className="details-section">
                                        <h4 className="section-title">Información de Pago</h4>
                                        <div className="payment-info">
                                            <div className="info-row">
                                                <span className="info-label">Estado</span>
                                                <span className={`info-value status-${getStatusColor(details.estado_pago)}`}>
                                                    {translateStatus(details.estado_pago)}
                                                </span>
                                            </div>
                                            <div className="info-row">
                                                <span className="info-label">Método</span>
                                                <span className="info-value">{details.metodo_pago || 'N/A'}</span>
                                            </div>
                                            {details.payment_id_mercadopago && (
                                                <div className="info-row">
                                                    <span className="info-label">ID de Pago</span>
                                                    <span className="info-value payment-id">{details.payment_id_mercadopago}</span>
                                                </div>
                                            )}
                                            <div className="info-row total-row">
                                                <span className="info-label">Total Pagado</span>
                                                <span className="info-value total-value">${formatPrice(details.monto_total)}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default OrderHistory;
