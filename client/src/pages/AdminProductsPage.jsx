// timba-sa/e-commerce/E-COMMERCE-50c1d7d8a49ac0891dda9940c53fddb-57630ff63/FRONTEND/src/pages/AdminProductsPage.jsx

import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { getProducts, deleteProduct } from '@/api/productsApi'; // <-- ¡ACÁ ESTÁ EL CAMBIO!
import { NotificationContext } from '../context/NotificationContext';
import Spinner from '../components/common/Spinner';

const AdminProductsPage = () => {
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
    if (!window.confirm('Are you sure you want to permanently delete this product?')) {
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

  if (loading) return <Spinner message="Loading inventory..." />;

  return (
    <div>
      <div className="admin-header">
        <h1>Product Management</h1>
        <Link to="/admin/products/new" className="add-product-btn">Add Product</Link>
      </div>

      {error && <h2 className="error-message" style={{marginBottom: '1rem', color: 'red'}}>{error}</h2>}
      
      <table className="admin-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Price</th>
            <th>Stock (Variants)</th>
            <th>Actions</th>
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
                    <Link to={`/admin/products/edit/${product.id}`} className="action-btn edit">Edit</Link>
                    <Link to={`/admin/products/${product.id}/variants`} className="action-btn variants">Variants</Link>
                    <button 
                      className="action-btn delete" 
                      onClick={() => handleDelete(product.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              );
            })
          ) : (
            <tr>
              <td colSpan="5" style={{ textAlign: 'center' }}>No products to display.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default AdminProductsPage;