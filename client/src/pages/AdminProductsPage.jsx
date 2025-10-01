import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getProducts, deleteProduct } from '@/api/productsApi';
import { NotificationContext } from '../context/NotificationContext';
import Spinner from '../components/common/Spinner';

const AdminProductsPage = () => {
  const { t } = useTranslation();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { notify } = useContext(NotificationContext);

  useEffect(() => {
    const fetchProducts = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await getProducts({ limit: 100 }); 
        setProducts(Array.isArray(data) ? data : []);
      } catch (err) {
        setError(err.message || 'Could not load products.');
        setProducts([]);
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, []);

  const handleDelete = async (productId) => {
    if (!window.confirm(t('admin_products_delete_confirm'))) {
      return;
    }
    try {
      await deleteProduct(productId);
      setProducts(products.filter(p => p.id !== productId));
      notify('Product deleted successfully.', 'success');
    } catch (err) {
      notify(`Error: ${err.detail || 'Could not delete product.'}` , 'error');
    }
  };

  if (loading) return <Spinner message={t('admin_products_loading')} />;

  return (
    <div>
      <div className="admin-header">
        <h1>{t('admin_products_title')}</h1>
        <Link to="/admin/products/new" className="add-product-btn">{t('admin_products_add_button')}</Link>
      </div>

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
          {products.length > 0 ? (
            products.map(product => {
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
              <td colSpan="5" style={{ textAlign: 'center' }}>{t('admin_products_none')}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default AdminProductsPage;