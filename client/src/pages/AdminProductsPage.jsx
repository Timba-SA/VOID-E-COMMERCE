// client/src/pages/AdminProductsPage.jsx

import React, { useState, useEffect, useContext, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getProducts, deleteProduct } from '@/api/productsApi';
import { getCategories } from '@/api/categoriesApi';
import { NotificationContext } from '../context/NotificationContext';
import Spinner from '../components/common/Spinner';

const AdminProductsPage = () => {
  const { t } = useTranslation();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(''); // El estado de error ahora es un string
  const { notify } = useContext(NotificationContext);

  const [categories, setCategories] = useState([]);
  const [categoryFilter, setCategoryFilter] = useState('');

  // --- ARREGLO: useEffect SEPARADOS para que no se pisen ---

  // Efecto N°1: Traer los productos
  useEffect(() => {
    const fetchProducts = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await getProducts({ limit: 500 }); 
        setProducts(Array.isArray(data) ? data : []);
      } catch (err) {
        // Guardamos solo el mensaje del error, no el objeto entero
        const errorMessage = err.response?.data?.detail || err.message || 'No se pudieron cargar los productos.';
        setError(errorMessage);
        setProducts([]);
        notify(errorMessage, 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, [notify]);

  // Efecto N°2: Traer las categorías (se ejecuta por separado)
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const categoriesData = await getCategories();
        setCategories(Array.isArray(categoriesData) ? categoriesData : []);
      } catch (err) {
        console.error("Error al cargar categorías para el filtro:", err);
        notify("No se pudieron cargar las categorías.", 'error');
      }
    };
    fetchCategories();
  }, [notify]);
  
  // --- FIN DEL ARREGLO ---

  const filteredProducts = useMemo(() => {
    if (!categoryFilter) {
      return products;
    }
    return products.filter(p => p.categoria_id === parseInt(categoryFilter));
  }, [products, categoryFilter]);


  const handleDelete = async (productId) => {
    if (!window.confirm(t('admin_products_delete_confirm'))) {
      return;
    }
    try {
      await deleteProduct(productId);
      setProducts(prevProducts => prevProducts.filter(p => p.id !== productId));
      notify('Producto eliminado con éxito.', 'success');
    } catch (err) {
      notify(`Error: ${err.detail || 'No se pudo eliminar el producto.'}` , 'error');
    }
  };

  if (loading) return <Spinner message={t('admin_products_loading')} />;

  return (
    <div>
      <div className="admin-header">
        <h1>{t('admin_products_title')}</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <select 
            onChange={(e) => setCategoryFilter(e.target.value)} 
            value={categoryFilter}
            style={{ padding: '0.5rem', fontSize: '0.9rem' }}
          >
            <option value="">Todas las Categorías</option>
            {categories.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.nombre}</option>
            ))}
          </select>
          <Link to="/admin/products/new" className="add-product-btn">{t('admin_products_add_button')}</Link>
        </div>
      </div>

      {/* Ahora el error se muestra como un texto y no rompe la página */}
      {error && <h2 className="error-message" style={{marginBottom: '1rem', color: 'red'}}>{error}</h2>}
      
      <table className="admin-table">
        <thead>
          <tr>
            <th>{t('admin_products_table_id')}</th>
            <th>{t('admin_products_table_name')}</th>
            <th>{t('admin_products_table_price')}</th>
            <th>{t('admin_products_table_stock')}</th>
            <th>{t('admin_products_table_actions')}</th>
          </tr>
        </thead>
        <tbody>
          {filteredProducts.length > 0 ? (
            filteredProducts.map(product => {
              const totalStockFromVariants = (product.variantes || []).reduce(
                (sum, variant) => sum + variant.cantidad_en_stock, 0
              );
              return (
                <tr key={product.id}>
                  <td>{product.id}</td>
                  <td>{product.nombre}</td>
                  <td>${product.precio}</td>
                  <td>{totalStockFromVariants}</td>
                  <td className="actions-cell">
                    <Link to={`/admin/products/edit/${product.id}`} className="action-btn edit">{t('admin_products_action_edit')}</Link>
                    <Link to={`/admin/products/${product.id}/variants`} className="action-btn variants">{t('admin_products_action_variants')}</Link>
                    <button 
                      className="action-btn delete" 
                      onClick={() => handleDelete(product.id)}
                    >
                      {t('admin_products_action_delete')}
                    </button>
                  </td>
                </tr>
              );
            })
          ) : (
            <tr>
              <td colSpan="5" style={{ textAlign: 'center' }}>
                {/* Mensaje inteligente: si hay filtro, dice una cosa, si no, otra */}
                {categoryFilter ? 'No hay productos en esta categoría.' : t('admin_products_none')}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default AdminProductsPage;