import React, { useState, useEffect, useContext } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getProductById } from '../api/productsApi'; // Usamos la pública para traer el producto
import { addVariantAPI, deleteVariantAPI } from '../api/adminApi';
import { NotificationContext } from '../context/NotificationContext';
import Spinner from '../components/common/Spinner';

const AdminProductVariantsPage = () => {
  const { t } = useTranslation();
  const { productId } = useParams();
  const { notify } = useContext(NotificationContext);

  const [product, setProduct] = useState(null);
  const [variants, setVariants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [newVariant, setNewVariant] = useState({
    tamanio: '',
    color: '',
    cantidad_en_stock: 0
  });

  useEffect(() => {
    const fetchProductAndVariants = async () => {
      try {
        const data = await getProductById(productId);
        setProduct(data);
        setVariants(data.variantes || []);
      } catch (err) {
        setError(err.detail || t('admin_variants_load_error'));
      } finally {
        setLoading(false);
      }
    };
    fetchProductAndVariants();
  }, [productId]);

  const handleNewVariantChange = (e) => {
    const { name, value, type } = e.target;
    setNewVariant(prev => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value, 10) || 0 : value
    }));
  };

  const handleAddVariant = async (e) => {
    e.preventDefault();
    try {
      const createdVariant = await addVariantAPI(productId, newVariant);
      setVariants([...variants, createdVariant]);
      setNewVariant({ tamanio: '', color: '', cantidad_en_stock: 0 });
      notify(t('admin_variants_added_success'), 'success');
    } catch (err) {
      notify(`${t('common_error')}: ${err.detail || t('admin_variants_create_error')}`, 'error');
    }
  };

  const handleDeleteVariant = async (variantId) => {
    if (!window.confirm(t('admin_variants_delete_confirm'))) {
      return;
    }
    try {
      await deleteVariantAPI(variantId);
      setVariants(variants.filter(v => v.id !== variantId));
      notify(t('admin_variants_deleted_success'), 'success');
    } catch (err) {
      notify(`${t('common_error')}: ${err.detail || t('admin_variants_delete_error')}`, 'error');
    }
  };

  if (loading) return <Spinner message={t('admin_variants_loading')} />;

  return (
    <div>
      <Link to="/admin/products" className="back-link">&larr; {t('admin_variants_back_to_products')}</Link>
      <div className="admin-header" style={{ justifyContent: 'center', marginBottom: '2rem' }}>
        <h1>{t('admin_variants_manage_title', { productName: product?.nombre })}</h1>
      </div>

      {error && <h2 className="error-message">{error}</h2>}

      <h3>{t('admin_variants_current_variants')}</h3>
      <table className="admin-table">
        <thead>
          <tr>
            <th>{t('admin_variants_table_id')}</th>
            <th>{t('admin_variants_table_size')}</th>
            <th>{t('admin_variants_table_color')}</th>
            <th>{t('admin_variants_table_stock')}</th>
            <th>{t('admin_variants_table_actions')}</th>
          </tr>
        </thead>
        <tbody>
          {variants.map(variant => (
            <tr key={variant.id}>
              <td>{variant.id}</td>
              <td>{variant.tamanio}</td>
              <td>{variant.color}</td>
              <td>{variant.cantidad_en_stock}</td>
              <td className="actions-cell">
                <button
                  className="action-btn delete"
                  onClick={() => handleDeleteVariant(variant.id)}
                >
                  {t('admin_variants_table_delete_button')}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <form onSubmit={handleAddVariant} className="admin-form" style={{marginTop: '3rem'}}>
        <h3 style={{borderTop: '1px solid #eee', paddingTop: '2rem'}}>{t('admin_variants_add_new_title')}</h3>
        <div className="form-grid">
            <div className="form-group">
                <label htmlFor="tamanio">{t('admin_variants_form_size')}</label>
                <input type="text" id="tamanio" name="tamanio" value={newVariant.tamanio} onChange={handleNewVariantChange} required />
            </div>
            <div className="form-group">
                <label htmlFor="color">{t('admin_variants_form_color')}</label>
                <input type="text" id="color" name="color" value={newVariant.color} onChange={handleNewVariantChange} required />
            </div>
            <div className="form-group">
                <label htmlFor="cantidad_en_stock">{t('admin_variants_form_stock')}</label>
                <input type="number" id="cantidad_en_stock" name="cantidad_en_stock" value={newVariant.cantidad_en_stock} onChange={handleNewVariantChange} required min="0" />
            </div>
        </div>
        <button type="submit" className="submit-btn">{t('admin_variants_add_button')}</button>
      </form>
    </div>
  );
};

export default AdminProductVariantsPage;