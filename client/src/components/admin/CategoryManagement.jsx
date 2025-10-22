import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCategoriesAdminAPI, createCategoryAPI, deleteCategoryAPI, updateCategoryAPI } from '@/api/adminApi';
import { getCategoryName } from '@/utils/categoryHelper';

const CategoryManagement = () => {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const [categoryName, setCategoryName] = useState('');
  const [categoryNameEs, setCategoryNameEs] = useState('');
  const [categoryNameEn, setCategoryNameEn] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [editingCategory, setEditingCategory] = useState(null);

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
      setCategoryNameEs('');
      setCategoryNameEn('');
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

  // Mutación para actualizar categoría
  const updateCategoryMutation = useMutation({
    mutationFn: ({ id, data }) => updateCategoryAPI(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminCategories'] });
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      setEditingCategory(null);
      setCategoryName('');
      setCategoryNameEs('');
      setCategoryNameEn('');
      setSuccess('¡Categoría actualizada con éxito!');
      setError('');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (error) => {
      console.error('Error al actualizar categoría:', error);
      setError(error.response?.data?.detail || error.detail || 'Error al actualizar la categoría');
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

    // Crear objeto con traducciones si se proporcionaron
    const categoryData = {
      nombre: categoryName.trim()
    };

    // Solo agregar nombre_i18n si al menos una traducción fue proporcionada
    if (categoryNameEs.trim() || categoryNameEn.trim()) {
      categoryData.nombre_i18n = {
        es: categoryNameEs.trim() || categoryName.trim(),
        en: categoryNameEn.trim() || categoryName.trim()
      };
    }

    if (editingCategory) {
      updateCategoryMutation.mutate({ id: editingCategory.id, data: categoryData });
    } else {
      createCategoryMutation.mutate(categoryData);
    }
  };

  const handleEdit = (category) => {
    setEditingCategory(category);
    setCategoryName(category.nombre);
    setCategoryNameEs(category.nombre_i18n?.es || '');
    setCategoryNameEn(category.nombre_i18n?.en || '');
  };

  const handleCancelEdit = () => {
    setEditingCategory(null);
    setCategoryName('');
    setCategoryNameEs('');
    setCategoryNameEn('');
    setError('');
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

      {/* Formulario de Creación/Edición */}
      <div style={{ backgroundColor: '#fff', border: '1px solid #dee2e6', borderRadius: '4px', padding: '1.5rem', marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '1rem', color: '#495057' }}>
          {editingCategory ? 'Editar Categoría' : 'Crear Nueva Categoría'}
        </h3>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '500', color: '#495057', marginBottom: '0.5rem' }}>
              Nombre de la Categoría (identificador)
            </label>
            <input
              type="text"
              value={categoryName}
              onChange={(e) => setCategoryName(e.target.value)}
              placeholder="Ej: remeras, camperas, etc."
              style={{ width: '100%', padding: '0.6rem', border: '1px solid #ced4da', borderRadius: '4px', fontSize: '0.9rem' }}
              required
            />
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '500', color: '#495057', marginBottom: '0.5rem' }}>
                Nombre en Español
              </label>
              <input
                type="text"
                value={categoryNameEs}
                onChange={(e) => setCategoryNameEs(e.target.value)}
                placeholder="Ej: Remeras"
                style={{ width: '100%', padding: '0.6rem', border: '1px solid #ced4da', borderRadius: '4px', fontSize: '0.9rem' }}
              />
            </div>
            
            <div>
              <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '500', color: '#495057', marginBottom: '0.5rem' }}>
                Nombre en Inglés
              </label>
              <input
                type="text"
                value={categoryNameEn}
                onChange={(e) => setCategoryNameEn(e.target.value)}
                placeholder="Ej: T-shirts"
                style={{ width: '100%', padding: '0.6rem', border: '1px solid #ced4da', borderRadius: '4px', fontSize: '0.9rem' }}
              />
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button
              type="submit"
              disabled={createCategoryMutation.isPending || updateCategoryMutation.isPending}
              className="add-product-btn"
              style={{ margin: 0 }}
            >
              {editingCategory 
                ? (updateCategoryMutation.isPending ? 'Actualizando...' : 'Actualizar Categoría')
                : (createCategoryMutation.isPending ? 'Creando...' : 'Crear Categoría')
              }
            </button>
            {editingCategory && (
              <button
                type="button"
                onClick={handleCancelEdit}
                className="form-button outline"
                style={{ margin: 0 }}
              >
                Cancelar
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Lista de Categorías */}
      <div className="table-responsive-wrapper">
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>Español</th>
              <th>Inglés</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {categories && categories.length > 0 ? (
              categories.map((category) => (
                <tr key={category.id}>
                  <td>{category.id}</td>
                  <td style={{ fontWeight: '500' }}>{category.nombre}</td>
                  <td>{category.nombre_i18n?.es || '-'}</td>
                  <td>{category.nombre_i18n?.en || '-'}</td>
                  <td className="actions-cell">
                    <button
                      onClick={() => handleEdit(category)}
                      className="action-btn edit"
                      style={{ marginRight: '0.5rem' }}
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => handleDelete(category.id, getCategoryName(category, i18n.language))}
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
                <td colSpan="5" style={{ textAlign: 'center', padding: '2rem', color: '#6c757d' }}>
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
