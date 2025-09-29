import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getProducts } from '../api/productsApi';
import { getCategories } from '../api/categoriesApi';
import FilterPanel from '@/components/common/FilterPanel.jsx';
import Spinner from '@/components/common/Spinner.jsx';
import ProductCard from '@/components/products/ProductCard.jsx';

// 1. DEFINIMOS LAS CATEGORÍAS DE HOMBRE, IGUAL QUE EN EL MENÚ.
const MENSWEAR_CATEGORIES = ['hoodies', 'jackets', 'shirts', 'pants'];

const ProductCardSkeleton = () => (
    <div className="catalog-product-card">
        <div className="catalog-product-image-container bg-gray-200 animate-pulse" style={{ backgroundColor: '#f0f0f0' }} />
        <div className="catalog-product-info mt-2">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2 animate-pulse" style={{ height: '1rem', backgroundColor: '#e0e0e0' }} />
            <div className="h-4 bg-gray-200 rounded w-1/2 animate-pulse" style={{ height: '1rem', backgroundColor: '#e0e0e0' }} />
        </div>
    </div>
);

const CatalogPage = () => {
    const { categoryName } = useParams();
    const [isFilterPanelOpen, setIsFilterPanelOpen] = useState(false);
    const [products, setProducts] = useState([]);
    const [categories, setCategories] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    const [filters, setFilters] = useState({
        talle: [],
        precio_min: 0,
        precio_max: 200000,
        sort_by: 'nombre_asc',
        color: [],
        categoria_id: '',
        skip: 0,
        limit: 12,
    });

    // 2. LÓGICA MEJORADA PARA MANEJAR "MENSWEAR" Y "WOMENSWEAR"
    useEffect(() => {
        const fetchCategoriesAndSetFilter = async () => {
            try {
                const allCategories = await getCategories();
                setCategories(allCategories);

                if (categoryName) {
                    let categoryIds = '';

                    if (categoryName.toLowerCase() === 'menswear') {
                        const menswearCats = allCategories.filter(c => MENSWEAR_CATEGORIES.includes(c.nombre.toLowerCase()));
                        categoryIds = menswearCats.map(c => c.id).join(',');
                    } else if (categoryName.toLowerCase() === 'womenswear') {
                        const womenswearCats = allCategories.filter(c => !MENSWEAR_CATEGORIES.includes(c.nombre.toLowerCase()));
                        categoryIds = womenswearCats.map(c => c.id).join(',');
                    } else {
                        const currentCategory = allCategories.find(c => c.nombre.toLowerCase() === categoryName.toLowerCase());
                        if (currentCategory) {
                            categoryIds = currentCategory.id.toString();
                        }
                    }
                    
                    // Solo actualizamos si encontramos IDs, sino, queda vacío para mostrar todo
                    setFilters(prev => ({ ...prev, categoria_id: categoryIds, skip: 0 }));
                } else {
                    // Si no hay categoryName, limpiamos el filtro para mostrar todos los productos
                    setFilters(prev => ({ ...prev, categoria_id: '', skip: 0 }));
                }
            } catch (err) {
                console.error("Failed to fetch categories", err);
            }
        };
        fetchCategoriesAndSetFilter();
    }, [categoryName]);

    const fetchProducts = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const params = { ...filters };
            
            if (params.talle.length > 0) params.talle = params.talle.join(',');
            else delete params.talle;
            
            if (params.color.length > 0) params.color = params.color.join(',');
            else delete params.color;

            if (!params.categoria_id) delete params.categoria_id;

            const data = await getProducts(params);
            setProducts(Array.isArray(data) ? data : []);
        } catch (err) {
            setError(err.message || 'Could not load products');
        } finally {
            setIsLoading(false);
        }
    }, [filters]);

    useEffect(() => {
        // Solo fetcheamos si ya tenemos las categorías cargadas y el filtro de ID definido
        if (categories.length > 0) {
            fetchProducts();
        }
        window.scrollTo(0, 0);
    }, [fetchProducts, categories]);

    useEffect(() => {
        document.body.style.overflow = isFilterPanelOpen ? 'hidden' : 'auto';
    }, [isFilterPanelOpen]);

    const handleFilterChange = (newFilters) => {
        setFilters(prev => ({ ...prev, ...newFilters, skip: 0 }));
    };
    
    const toggleFilterPanel = () => setIsFilterPanelOpen(!isFilterPanelOpen);

    // 3. MEJORAMOS EL TÍTULO DE LA PÁGINA
    const getPageTitle = () => {
        if (!categoryName) return 'CATALOG';
        if (categoryName.toLowerCase() === 'menswear') return 'MENSWEAR';
        if (categoryName.toLowerCase() === 'womenswear') return 'WOMENSWEAR';
        return categoryName.replace('-', ' ').toUpperCase();
    };

    return (
        <>
            <main className="catalog-container">
                <div className="catalog-header">
                    <h1 className="catalog-title">{getPageTitle()}</h1>
                    <div className="catalog-controls">
                        <button onClick={toggleFilterPanel} className="filters-link">FILTERS &gt;</button>
                    </div>
                </div>

                {isLoading ? (
                  <div className="catalog-product-grid">
                      {Array.from({ length: 8 }).map((_, i) => <ProductCardSkeleton key={i} />)}
                  </div>
                ) : error ? (
                  <p className="loading-text">{error}</p>
                ) : products.length > 0 ? (
                  <div className="catalog-product-grid">
                      {products.map(product => <ProductCard product={product} key={product.id || product._id} />)}
                  </div>
                ) : (
                    <p className="loading-text">No products found with these filters.</p>
                )}
            </main>
            
            <div className={`filter-panel-overlay ${isFilterPanelOpen ? 'open' : ''}`} onClick={toggleFilterPanel} />
            <FilterPanel 
                isOpen={isFilterPanelOpen} 
                onClose={toggleFilterPanel} 
                onFilterChange={handleFilterChange}
                initialFilters={filters}
                categories={categories}
            />
        </>
    );
};

export default CatalogPage;