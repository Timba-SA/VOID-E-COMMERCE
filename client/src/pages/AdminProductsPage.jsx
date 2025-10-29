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
  const [error, setError] = useState('');
  const { notify } = useContext(NotificationContext);

  const [categories, setCategories] = useState([]);
  const [categoryFilter, setCategoryFilter] = useState('');

  useEffect(() => {
    const fetchProducts = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await getProducts({ limit: 500 }); 
        setProducts(Array.isArray(data) ? data : []);
      } catch (err) {
        const errorMessage = err.response?.data?.detail || err.message || t('admin_products_load_error');
        setError(errorMessage);
        setProducts([]);
        notify(errorMessage, 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, [notify]);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const categoriesData = await getCategories();
        setCategories(Array.isArray(categoriesData) ? categoriesData : []);
      } catch (err) {
        console.error(t('admin_categories_filter_error'), err);
        notify(t('admin_categories_load_error'), 'error');
      }
    };
    fetchCategories();
  }, [notify]);
  
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
      notify(t('admin_products_delete_success'), 'success');
    } catch (err) {
      notify(`Error: ${err.detail || t('admin_products_delete_error')}` , 'error');
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
            <option value="">{t('admin_products_all_categories')}</option>
            {categories.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.nombre}</option>
            ))}
          </select>
          <Link to="/admin/products/new" className="add-product-btn">{t('admin_products_add_button')}</Link>
        </div>
      </div>

      {error && <h2 className="error-message" style={{marginBottom: '1rem', color: 'red'}}>{error}</h2>}
      
      <div className="table-responsive-wrapper">
        <table className="admin-table admin-products-table">
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
                  {categoryFilter ? 'No hay productos en esta categoría.' : t('admin_products_none')}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AdminProductsPage;