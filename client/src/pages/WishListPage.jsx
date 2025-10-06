// En client/src/pages/WishlistPage.jsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getWishlistAPI } from '../api/wishListApi';
import ProductCard from '../components/products/ProductCard';
import Spinner from '../components/common/Spinner';

const WishlistPage = () => {
  const { data: wishlist, isLoading, error } = useQuery({
    queryKey: ['wishlist'],
    queryFn: getWishlistAPI
  });

  if (isLoading) {
    return <Spinner message="Cargando tus favoritos..." />;
  }

  if (error) {
    return <p className="loading-text">Error al cargar tu wishlist.</p>;
  }

  return (
    <main className="catalog-container">
      <div className="catalog-header">
        <h1 className="catalog-title">Mi Wishlist</h1>
      </div>

      {wishlist && wishlist.length > 0 ? (
        <div className="catalog-product-grid">
          {wishlist.map(product => (
            <ProductCard product={product} key={product.id} />
          ))}
        </div>
      ) : (
        <p className="loading-text">Todavía no guardaste ningún producto en tu wishlist.</p>
      )}
    </main>
  );
};

export default WishlistPage;