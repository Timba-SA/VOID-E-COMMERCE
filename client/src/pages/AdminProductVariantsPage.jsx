// En FRONTEND/src/pages/AdminProductVariantsPage.jsx
import React, { useState, useEffect, useContext } from 'react';
import { useParams, Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { NotificationContext } from '../context/NotificationContext';
import Spinner from '../components/common/Spinner';

const AdminProductVariantsPage = () => {
  const { productId } = useParams();
  const { token } = useContext(AuthContext);
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
        const response = await fetch(`http://127.0.0.1:8000/api/products/${productId}`);
        if (!response.ok) throw new Error('No se pudo cargar el producto.');
        const data = await response.json();
        setProduct(data);
        setVariants(data.variantes || []);
      } catch (err) {
        setError(err.message);
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
      [name]: type === 'number' ? parseInt(value) || 0 : value
    }));
  };

  const handleAddVariant = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/products/${productId}/variants`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newVariant)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'No se pudo crear la variante.');
      }

      const createdVariant = await response.json();
      setVariants([...variants, createdVariant]);
      setNewVariant({ tamanio: '', color: '', cantidad_en_stock: 0 });
      notify('Variante agregada con éxito.', 'success');

    } catch (err) {
      setError(err.message);
      notify(`Error: ${err.message}`, 'error');
    }
  };

  const handleDeleteVariant = async (variantId) => {
    if (!window.confirm('¿Estás seguro de que quieres eliminar esta variante?')) {
      return;
    }
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/admin/products/${productId}/variants/${variantId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'No se pudo eliminar la variante.');
      }
      setVariants(variants.filter(v => v.id !== variantId));
      notify('Variante eliminada.', 'success');
    } catch (err) {
      setError(err.message);
      notify(`Error: ${err.message}`, 'error');
    }
  };

  if (loading) return <Spinner message="Cargando variantes..." />;
  if (error) return <h2 className="error-message">Error: {error}</h2>;

  return (
    <div>
      <Link to="/admin/products">&larr; Volver a Productos</Link>
      <div className="admin-header">
        <h1>Gestionar Variantes de "{product?.nombre}"</h1>
      </div>

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

      <form onSubmit={handleAddVariant} className="admin-form" style={{marginTop: '2rem'}}>
        <h3>Añadir Nueva Variante</h3>
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
                <input type="number" id="cantidad_en_stock" name="cantidad_en_stock" value={newVariant.cantidad_en_stock} onChange={handleNewVariantChange} required />
            </div>
        </div>
        <button type="submit" className="submit-btn">Añadir Variante</button>
      </form>
    </div>
  );
};

export default AdminProductVariantsPage;