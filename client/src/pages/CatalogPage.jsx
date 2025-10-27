import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getProducts } from '../api/productsApi';
import { getCategories } from '../api/categoriesApi';
import { getCategoryName } from '../utils/categoryHelper';
import FilterPanel from '@/components/common/FilterPanel.jsx';
import Spinner from '@/components/common/Spinner.jsx';
import ProductCard from '@/components/products/ProductCard.jsx';

// Categorías de hombre por su nombre en español (nombre original en DB)
const MENSWEAR_CATEGORIES = ['hoodies', 'camperas', 'remeras', 'pantalones'];

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
    const { t, i18n } = useTranslation();
    const [isFilterPanelOpen, setIsFilterPanelOpen] = useState(false);
    const [products, setProducts] = useState([]);
    const [categories, setCategories] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [isNextPageAvailable, setIsNextPageAvailable] = useState(true);

    const PAGE_LIMIT = 8; // <-- ¡ACÁ ESTÁ EL CAMBIO, PAPÁ!

    const [filters, setFilters] = useState({
        talle: [],
        precio_min: 0,
        precio_max: 200000,
        sort_by: 'nombre_asc',
        color: [],
        categoria_id: '',
    });

    useEffect(() => {
        const fetchCategoriesAndSetFilter = async () => {
            try {
                const allCategories = await getCategories();
                setCategories(allCategories);
                let categoryIds = '';
                if (categoryName) {
                    if (categoryName.toLowerCase() === 'menswear') {
                        categoryIds = allCategories.filter(c => MENSWEAR_CATEGORIES.includes(c.nombre.toLowerCase())).map(c => c.id).join(',');
                    } else if (categoryName.toLowerCase() === 'womenswear') {
                        categoryIds = allCategories.filter(c => !MENSWEAR_CATEGORIES.includes(c.nombre.toLowerCase())).map(c => c.id).join(',');
                    } else {
                        const currentCategory = allCategories.find(c => c.nombre.toLowerCase() === categoryName.toLowerCase());
                        if (currentCategory) categoryIds = currentCategory.id.toString();
                    }
                }
                setFilters(prev => ({ ...prev, categoria_id: categoryIds }));
                setCurrentPage(1);
                // Limpiar productos para forzar recarga
                setProducts([]);
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
            const params = { 
                ...filters,
                skip: (currentPage - 1) * PAGE_LIMIT,
                limit: PAGE_LIMIT
            };
            
            if (params.talle.length > 0) params.talle = params.talle.join(',');
            else delete params.talle;
            
            if (params.color.length > 0) params.color = params.color.join(',');
            else delete params.color;

            if (!params.categoria_id) delete params.categoria_id;

            const data = await getProducts(params);
            setProducts(Array.isArray(data) ? data : []);
            setIsNextPageAvailable(data.length === PAGE_LIMIT);
        } catch (err) {
            setError(err.message || 'No se pudieron cargar los productos.');
        } finally {
            setIsLoading(false);
        }
    }, [filters, currentPage, PAGE_LIMIT]);

    useEffect(() => {
        fetchProducts();
        window.scrollTo(0, 0);
    }, [fetchProducts]);

    const handleFilterChange = (newFilters) => {
        setFilters(prev => ({ ...prev, ...newFilters }));
        setCurrentPage(1);
    };

    const handlePageChange = (newPage) => {
        if (newPage < 1) return;
        setCurrentPage(newPage);
    };
    
    const toggleFilterPanel = () => setIsFilterPanelOpen(!isFilterPanelOpen);

    const getPageTitle = () => {
        if (!categoryName) return t('catalog_all_products');
        if (categoryName.toLowerCase() === 'menswear') return t('catalog_menswear');
        if (categoryName.toLowerCase() === 'womenswear') return t('catalog_womenswear');
        
        // Buscar la categoría y obtener su nombre traducido
        const category = categories.find(c => 
            c.nombre.toLowerCase() === categoryName.toLowerCase()
        );
        
        if (category) {
            return getCategoryName(category, i18n.language);
        }
        
        return t(categoryName.toLowerCase(), categoryName.replace('-', ' ').toUpperCase());
    };
    
    // Efecto para actualizar título cuando cambie el idioma
    useEffect(() => {
        // Forzar actualización del título
        const title = getPageTitle();
        document.title = `${title} - VOID`;
    }, [i18n.language, categoryName, categories]);

    const pageNumbers = [1, 2, 3, 4, 5]; 

    return (
        <>
            <main className="catalog-container">
                <div className="catalog-header">
                    <h1 className="catalog-title">{getPageTitle()}</h1>
                    <button onClick={toggleFilterPanel} className="filters-link">{t('catalog_filters')} &gt;</button>
                </div>

                {isLoading ? (
                  <div className="catalog-product-grid">
                      {Array.from({ length: 8 }).map((_, i) => <ProductCardSkeleton key={i} />)}
                  </div>
                ) : error ? (
                  <p className="loading-text">{error}</p>
                ) : products.length > 0 ? (
                  <div className="catalog-product-grid">
                      {products.map(product => <ProductCard product={product} key={product.id} />)}
                  </div>
                ) : (
                    <p className="loading-text">{t('catalog_no_products', 'No se encontraron productos con estos filtros.')}</p>
                )}

                <div className="pagination-controls">
                    <button onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1} className="pagination-arrow">
                        &lt; {t('catalog_previous')}
                    </button>
                    <div className="pagination-numbers">
                        {pageNumbers.map(number => (
                            <button 
                                key={number}
                                onClick={() => handlePageChange(number)}
                                className={`pagination-number ${currentPage === number ? 'active' : ''}`}
                            >
                                {number}
                            </button>
                        ))}
                    </div>
                    <button onClick={() => handlePageChange(currentPage + 1)} disabled={!isNextPageAvailable} className="pagination-arrow">
                        {t('catalog_next')} &gt;
                    </button>
                </div>
            </main>
            
            <div className={`filter-panel-overlay ${isFilterPanelOpen ? 'open' : ''}`} onClick={toggleFilterPanel} />
            <FilterPanel 
                isOpen={isFilterPanelOpen} 
                onClose={toggleFilterPanel} 
                onFilterChange={handleFilterChange}
                initialFilters={filters}
            />
        </>
    );
};

export default CatalogPage;