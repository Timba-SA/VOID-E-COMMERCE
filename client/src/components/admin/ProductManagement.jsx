// En FRONTEND/src/components/admin/ProductManagement.jsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
// Importamos las funciones de la API centralizadas
import { getProducts, createProduct, deleteProduct } from '@/api/productsApi';

const ProductManagement = () => {
  const queryClient = useQueryClient();
  const [productData, setProductData] = useState({
    nombre: '',
    descripcion: '',
    precio: '',
    sku: '',
    stock: '',
    categoria_id: 1, // Ejemplo
  });
  const [imageFile, setImageFile] = useState(null);

  // Usamos getProducts para el query
  const { data: products, isLoading } = useQuery({
    queryKey: ['adminProducts'],
    queryFn: () => getProducts(), // Llamamos a la función importada
  });

  // Mutación para crear productos
  const createProductMutation = useMutation({
    mutationFn: createProduct, // Usamos la función importada
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminProducts'] });
      // Aquí podrías limpiar el formulario si quieres
      alert("¡Producto creado con éxito!");
    },
    onError: (error) => {
      console.error("Error al crear producto:", error);
      alert("Error: " + (error.response?.data?.detail || error.message));
    }
  });

  // --- ¡NUEVO! Mutación para eliminar productos ---
  const deleteProductMutation = useMutation({
    mutationFn: deleteProduct, // Usamos la función importada
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminProducts'] });
      alert("Producto eliminado con éxito");
    },
    onError: (error) => {
      console.error("Error al eliminar producto:", error);
      alert("Error: " + (error.response?.data?.detail || error.message));
    }
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setProductData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e) => {
    setImageFile(e.target.files[0]);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!imageFile) {
      alert("Por favor, selecciona una imagen para el producto.");
      return;
    }

    const formData = new FormData();
    formData.append('images', imageFile); // El backend espera 'images'

    // Añadimos el resto de los datos del producto
    for (const key in productData) {
      formData.append(key, productData[key]);
    }

    createProductMutation.mutate(formData);
  };

  // --- ¡NUEVO! Handler para el borrado ---
  const handleDelete = (productId) => {
    if (window.confirm("¿Estás seguro de que quieres eliminar este producto?")) {
      deleteProductMutation.mutate(productId);
    }
  };

  return (
    <div>
      <h2>Gestión de Productos</h2>

      {/* Formulario de Creación */}
      <form onSubmit={handleSubmit} style={{ border: '1px solid #ccc', padding: '1rem', marginBottom: '2rem' }}>
        <h3>Crear Nuevo Producto</h3>
        <input type="text" name="nombre" placeholder="Nombre" onChange={handleInputChange} required />
        <input type="text" name="sku" placeholder="SKU" onChange={handleInputChange} required />
        <input type="number" name="precio" placeholder="Precio" onChange={handleInputChange} required />
        <input type="number" name="stock" placeholder="Stock" onChange={handleInputChange} required />
        <textarea name="descripcion" placeholder="Descripción" onChange={handleInputChange}></textarea>
        
        <div>
          <label>Imagen del Producto</label>
          <input type="file" onChange={handleFileChange} required accept="image/*" />
        </div>
        
        <button type="submit" disabled={createProductMutation.isPending}>
          {createProductMutation.isPending ? 'Creando...' : 'Crear Producto'}
        </button>
      </form>

      {/* Lista de Productos */}
      <h3>Productos Existentes</h3>
      {isLoading ? <p>Cargando productos...</p> : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {products?.map(p => (
            <li 
              key={p.id} 
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between', 
                padding: '0.5rem', 
                borderBottom: '1px solid #eee' 
              }}
            >
              <div>
                <img src={p.urls_imagenes?.[0]} alt={p.nombre} width="50" style={{ marginRight: '1rem', verticalAlign: 'middle' }} />
                <span style={{ fontWeight: 'bold' }}>{p.nombre}</span> ({p.sku})
              </div>
              {/* --- ¡NUEVO! Botón de eliminar --- */}
              <button 
                onClick={() => handleDelete(p.id)} 
                disabled={deleteProductMutation.isPending}
                style={{
                  backgroundColor: '#dc3545',
                  color: 'white',
                  border: 'none',
                  padding: '0.3rem 0.6rem',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Eliminar
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ProductManagement;