import React from 'react';
import { Link } from 'react-router-dom';

const ProductCard = ({ product }) => {
  // 1. Nos aseguramos de que el producto exista para no romper todo.
  if (!product) {
    return null;
  }

  // 2. --- ¡ACÁ ESTÁ EL GOL DE MESSI A MÉXICO! ---
  //    Agarramos el ID, se llame 'id' o '_id'. El que venga, lo usamos.
  const productId = product.id || product._id;

  // Si después de todo, sigue sin haber ID, mejor no mostramos nada.
  if (!productId) {
    console.error("Producto sin ID, no se puede renderizar:", product);
    return null; 
  }

  // El resto del código como lo tenías...
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

  return (
    <div className="catalog-product-card product-card">
      {/* 3. Y acá usamos el 'productId' que encontramos. Se acabaron los 'undefined'. */}
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