import React, { useState, useEffect, useContext } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getProductById } from '../api/productsApi'; // Usamos la pública para traer el producto
import { addVariantAPI, deleteVariantAPI } from '../api/adminApi';
import { NotificationContext } from '../context/NotificationContext';
import Spinner from '../components/common/Spinner';

const AdminProductVariantsPage = () => {
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
        setError(err.detail || 'No se pudo cargar el producto y sus variantes.');
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
      notify('Variante agregada con éxito.', 'success');
    } catch (err) {
      notify(`Error: ${err.detail || 'No se pudo crear la variante.'}`, 'error');
    }
  };

  const handleDeleteVariant = async (variantId) => {
    if (!window.confirm('¿Estás seguro de que quieres eliminar esta variante?')) {
      return;
    }
    try {
      await deleteVariantAPI(variantId);
      setVariants(variants.filter(v => v.id !== variantId));
      notify('Variante eliminada.', 'success');
    } catch (err) {
      notify(`Error: ${err.detail || 'No se pudo eliminar la variante.'}`, 'error');
    }
  };

  if (loading) return <Spinner message="Cargando variantes..." />;

  return (
    <div>
      <Link to="/admin/products" className="back-link">&larr; Volver a Productos</Link>
      <div className="admin-header" style={{ justifyContent: 'center', marginBottom: '2rem' }}>
        <h1>Gestionar Variantes de "{product?.nombre}"</h1>
      </div>

      {error && <h2 className="error-message">{error}</h2>}

      <h3>Variantes Actuales</h3>
      <table className="admin-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Talle</th>
            <th>Color</th>
            <th>Stock</th>
            <th>Acciones</th>
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
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <form onSubmit={handleAddVariant} className="admin-form" style={{marginTop: '3rem'}}>
        <h3 style={{borderTop: '1px solid #eee', paddingTop: '2rem'}}>Añadir Nueva Variante</h3>
        <div className="form-grid">
            <div className="form-group">
                <label htmlFor="tamanio">Talle</label>
                <input type="text" id="tamanio" name="tamanio" value={newVariant.tamanio} onChange={handleNewVariantChange} required />
            </div>
            <div className="form-group">
                <label htmlFor="color">Color</label>
                <input type="text" id="color" name="color" value={newVariant.color} onChange={handleNewVariantChange} required />
            </div>
            <div className="form-group">
                <label htmlFor="cantidad_en_stock">Stock</label>
                <input type="number" id="cantidad_en_stock" name="cantidad_en_stock" value={newVariant.cantidad_en_stock} onChange={handleNewVariantChange} required min="0" />
            </div>
        </div>
        <button type="submit" className="submit-btn">Añadir Variante</button>
      </form>
    </div>
  );
};

export default AdminProductVariantsPage;