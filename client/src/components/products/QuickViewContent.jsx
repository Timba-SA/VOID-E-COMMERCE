import React from 'react';
import { Link } from 'react-router-dom';

// --- FUNCIÓN CLAVE: La misma solución ---
const getImageUrl = (urls_imagenes) => {
  if (!urls_imagenes) {
    return '/img/placeholder.jpg';
  }
  if (typeof urls_imagenes === 'string' && urls_imagenes.startsWith('["')) {
    try {
      const parsedUrls = JSON.parse(urls_imagenes);
      return parsedUrls[0] || '/img/placeholder.jpg';
    } catch (e) {
      return '/img/placeholder.jpg';
    }
  }
  return urls_imagenes;
};

const QuickViewContent = ({ product, onClose }) => {
    if (!product) return null;

    const formatPrice = (price) => {
        return new Intl.NumberFormat('es-AR', {
          style: 'currency',
          currency: 'ARS',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(price).replace("ARS", "$").trim();
    };

    return (
        <div className="quick-view-content-wrapper">
            <div className="quick-view-image-container">
                {/* --- ¡AQUÍ ESTÁ EL CAMBIO! --- */}
                <img src={getImageUrl(product.urls_imagenes)} alt={product.nombre} />
            </div>
            <div className="quick-view-info">
                <h3 className="quick-view-name">{product.nombre}</h3>
                <p className="quick-view-price">{formatPrice(product.precio)} ARS</p>
                <div className="quick-view-actions">
                    <Link to={`/product/${product.id}`} onClick={onClose} className="quick-view-link-button">
                        VIEW PRODUCT
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default QuickViewContent;