// En client/src/components/products/ProductCard.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../../stores/useAuthStore';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getWishlistAPI, addToWishlistAPI, removeFromWishlistAPI } from '../../api/wishListApi';
import { Heart } from 'lucide-react';

const ProductCard = ({ product, displayMode }) => {
  const { isAuthenticated } = useAuthStore();
  const queryClient = useQueryClient();

  const { data: wishlist } = useQuery({
    queryKey: ['wishlist'],
    queryFn: getWishlistAPI,
    enabled: isAuthenticated,
  });

  const isWishlisted = React.useMemo(() => 
    wishlist?.some(item => item.id === product?.id),
    [wishlist, product]
  );

  const addToWishlistMutation = useMutation({
    mutationFn: addToWishlistAPI,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] });
    },
  });

  const removeFromWishlistMutation = useMutation({
    mutationFn: removeFromWishlistAPI,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] });
    },
  });

  const handleWishlistToggle = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) return;

    if (isWishlisted) {
      removeFromWishlistMutation.mutate(product.id);
    } else {
      addToWishlistMutation.mutate(product.id);
    }
  };

  if (!product) return null;
  const productId = product.id || product._id;
  if (!productId) return null;

  const imageUrl = product.urls_imagenes && product.urls_imagenes.length > 0
    ? product.urls_imagenes[0]
    : 'https://via.placeholder.com/300x400';

  const formatPrice = (price) => {
    if (typeof price !== 'number') return '$--';
    return new Intl.NumberFormat('es-AR', {
      style: 'currency', currency: 'ARS',
      minimumFractionDigits: 0, maximumFractionDigits: 0,
    }).format(price);
  };

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

  return (
    <div className="catalog-product-card">
      <Link to={`/product/${productId}`} className="catalog-product-link">
        <div className="catalog-product-image-container">
          <img src={imageUrl} alt={product.nombre} className="catalog-product-image" />
          {isAuthenticated && (
            <button onClick={handleWishlistToggle} className="wishlist-button">
              <Heart 
                size={20} 
                className={isWishlisted ? 'wishlisted' : ''}
              />
            </button>
          )}
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