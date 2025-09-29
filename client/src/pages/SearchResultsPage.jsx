import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { getProducts } from '../api/productsApi';
import Spinner from '../components/common/Spinner';

const SearchResultsPage = () => {
    const [searchParams] = useSearchParams();
    const query = searchParams.get('q');

    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!query) {
            setProducts([]);
            setLoading(false);
            return;
        }

        const fetchSearchResults = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await getProducts({ q: query, limit: 100 });
                setProducts(data);
            } catch (err) {
                setError('Error searching for products.');
            }
            setLoading(false);
        };

        fetchSearchResults();
    }, [query]);

    const formatPrice = (price) => {
        return new Intl.NumberFormat('en-US', {
          style: 'currency', currency: 'ARS',
          minimumFractionDigits: 0, maximumFractionDigits: 0,
        }).format(price).replace("ARS", "$").trim();
    };

    return (
        <main className="catalog-container">
            <div className="catalog-header">
                <h1 className="catalog-title">Results for: "{query}"</h1>
            </div>

            {loading && <Spinner message="Searching..." />}
            {error && <p className="loading-text">{error}</p>}
            
            {!loading && !error && products?.length === 0 && (
                <p className="loading-text">No products were found for your search.</p>
            )}

            {products && products.length > 0 && (
                <div className="catalog-product-grid">
                    {products.map(product => (
                        <Link to={`/product/${product.id}`} className="catalog-product-card" key={product.id}>
                            <div className="catalog-product-image-container">
                                <img 
                                    src={product.urls_imagenes?.[0] || '/img/placeholder.jpg'} 
                                    alt={product.nombre} 
                                    className="catalog-product-image"
                                />
                            </div>
                            <div className="catalog-product-info">
                                <h3 className="catalog-product-name">{product.nombre}</h3>
                                <p className="catalog-product-price">{formatPrice(product.precio)}</p>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </main>
    );
};

export default SearchResultsPage;