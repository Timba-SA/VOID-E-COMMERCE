// En client/src/components/products/ProductCard.jsx

import React from 'react';
import { Link } from 'react-router-dom';

const ProductCard = ({ product, displayMode }) => {
  if (!product) {
    return null;
  }

  const productId = product.id || product._id;
  if (!productId) {
    console.error("Producto sin ID, no se puede renderizar:", product);
    return null;
  }

  const imageUrl = product.urls_imagenes && product.urls_imagenes.length > 0
    ? product.urls_imagenes[0]
    : 'https://via.placeholder.com/300x400';

  const formatPrice = (price) => {
    if (typeof price !== 'number') {
        return '$--';
    }
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  // --- ¡ACÁ ESTÁ LA LÓGICA NUEVA! ---
  if (displayMode === 'imageOnly') {
    return (
      <div className="product-card-home">
        <Link to={`/product/${productId}`} className="product-link-image-only">
          <div className="product-image-container-home">
            <img src={imageUrl} alt={product.nombre} className="product-image-home" />
          </div>
        </Link>
      </div>
    );
  }

  // --- ESTA ES LA VISTA NORMAL PARA EL RESTO DE LA APP (CATÁLOGO, ETC.) ---
  return (
    <div className="catalog-product-card">
      <Link to={`/product/${productId}`} className="catalog-product-link">
        <div className="catalog-product-image-container">
          <img src={imageUrl} alt={product.nombre} className="catalog-product-image" />
        </div>
        <div className="catalog-product-info">
          <h3 className="catalog-product-name">{product.nombre}</h3>
          <p className="catalog-product-price">{formatPrice(product.precio)}</p>
        </div>
      </Link>
    </div>
  );
};

export default ProductCard;