import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCategoriesAdminAPI, createCategoryAPI, deleteCategoryAPI } from '@/api/adminApi';

const CategoryManagement = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [categoryName, setCategoryName] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Query para obtener las categorías
  const { data: categories, isLoading } = useQuery({
    queryKey: ['adminCategories'],
    queryFn: getCategoriesAdminAPI,
  });

  // Mutación para crear categoría
  const createCategoryMutation = useMutation({
    mutationFn: createCategoryAPI,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminCategories'] });
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      setCategoryName('');
      setSuccess('¡Categoría creada con éxito!');
      setError('');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (error) => {
      console.error('Error al crear categoría:', error);
      setError(error.response?.data?.detail || error.detail || 'Error al crear la categoría');
      setSuccess('');
    }
  });

  // Mutación para eliminar categoría
  const deleteCategoryMutation = useMutation({
    mutationFn: deleteCategoryAPI,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminCategories'] });
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      setSuccess('Categoría eliminada con éxito');
      setError('');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (error) => {
      console.error('Error al eliminar categoría:', error);
      setError(error.response?.data?.detail || error.detail || 'Error al eliminar la categoría');
      setSuccess('');
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    
    if (!categoryName.trim()) {
      setError('El nombre de la categoría no puede estar vacío');
      return;
    }

    createCategoryMutation.mutate({ nombre: categoryName.trim() });
  };

  const handleDelete = (categoryId, categoryName) => {
    if (window.confirm(`¿Estás seguro de que quieres eliminar la categoría "${categoryName}"?\n\nSolo se puede eliminar si no tiene productos asociados.`)) {
      setError('');
      setSuccess('');
      deleteCategoryMutation.mutate(categoryId);
    }
  };

  if (isLoading) {
    return (
      <div>
        <div className="admin-header">
          <h1>Gestión de Categorías</h1>
        </div>
        <p>Cargando categorías...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="admin-header">
        <h1>Gestión de Categorías</h1>
      </div>

      {/* Mensajes de feedback */}
      {error && (
        <div className="error-message" style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#f8d7da', color: '#721c24', borderRadius: '4px', border: '1px solid #f5c6cb' }}>
          {error}
        </div>
      )}
      {success && (
        <div className="success-message" style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#d4edda', color: '#155724', borderRadius: '4px', border: '1px solid #c3e6cb' }}>
          {success}
        </div>
      )}

      {/* Formulario de Creación */}
      <div style={{ backgroundColor: '#fff', border: '1px solid #dee2e6', borderRadius: '4px', padding: '1.5rem', marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '1rem', color: '#495057' }}>Crear Nueva Categoría</h3>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
          <div style={{ flex: '1' }}>
            <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '500', color: '#495057', marginBottom: '0.5rem' }}>
              Nombre de la Categoría
            </label>
            <input
              type="text"
              value={categoryName}
              onChange={(e) => setCategoryName(e.target.value)}
              placeholder="Ej: Ropa Deportiva, Accesorios, etc."
              style={{ width: '100%', padding: '0.6rem', border: '1px solid #ced4da', borderRadius: '4px', fontSize: '0.9rem' }}
              required
            />
          </div>
          <button
            type="submit"
            disabled={createCategoryMutation.isPending}
            className="add-product-btn"
            style={{ margin: 0, whiteSpace: 'nowrap' }}
          >
            {createCategoryMutation.isPending ? 'Creando...' : 'Crear Categoría'}
          </button>
        </form>
      </div>

      {/* Lista de Categorías */}
      <div className="table-responsive-wrapper">
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {categories && categories.length > 0 ? (
              categories.map((category) => (
                <tr key={category.id}>
                  <td>{category.id}</td>
                  <td style={{ fontWeight: '500' }}>{category.nombre}</td>
                  <td className="actions-cell">
                    <button
                      onClick={() => handleDelete(category.id, category.nombre)}
                      disabled={deleteCategoryMutation.isPending}
                      className="action-btn delete"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="3" style={{ textAlign: 'center', padding: '2rem', color: '#6c757d' }}>
                  No hay categorías creadas aún.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CategoryManagement;
