import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProductById, createProduct, updateProduct } from '../api/productsApi';
import { getCategories } from '../api/categoriesApi';
import { NotificationContext } from '../context/NotificationContext';
import Spinner from '../components/common/Spinner';
import {
    DndContext,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
} from '@dnd-kit/core';
import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    useSortable,
    rectSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

const SortableImage = ({ id, src, onRemove }) => {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
    } = useSortable({ id });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        position: 'relative',
        border: '1px solid #ddd',
        padding: '5px',
        touchAction: 'none',
    };

    return (
        <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
            <img src={src} alt="preview" width="80" height="80" style={{ objectFit: 'cover' }} />
            <button
                type="button"
                onClick={() => onRemove(src)}
                style={{
                    position: 'absolute', top: '-10px', right: '-10px', background: 'red', color: 'white',
                    border: 'none', borderRadius: '50%', width: '20px', height: '20px',
                    cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}
            >
                X
            </button>
        </div>
    );
};


const AdminProductFormPage = () => {
    const { productId } = useParams();
    const navigate = useNavigate();
    const { notify } = useContext(NotificationContext);

    const [productData, setProductData] = useState({
        nombre: '',
        descripcion: '',
        precio: 0,
        sku: '',
        stock: 0,
        categoria_id: '',
        material: '',
        talle: '',
        color: '',
    });

    const [categories, setCategories] = useState([]);
    const [imageFiles, setImageFiles] = useState([]);
    const [visibleImages, setVisibleImages] = useState([]);
    const [imagesToDelete, setImagesToDelete] = useState([]);
    const [loading, setLoading] = useState(false);
    const isEditing = Boolean(productId);

    const sensors = useSensors(
        useSensor(PointerSensor),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    useEffect(() => {
        const fetchInitialData = async () => {
            setLoading(true);
            try {
                const categoriesData = await getCategories();
                setCategories(categoriesData);

                if (isEditing) {
                    const productToEdit = await getProductById(productId);
                    setProductData({
                        nombre: productToEdit.nombre || '',
                        descripcion: productToEdit.descripcion || '',
                        precio: productToEdit.precio || 0,
                        sku: productToEdit.sku || '',
                        stock: productToEdit.stock || 0,
                        categoria_id: productToEdit.categoria_id || '',
                        material: productToEdit.material || '',
                        talle: productToEdit.talle || '',
                        color: productToEdit.color || '',
                    });
                    setVisibleImages(productToEdit.urls_imagenes || []);
                }
            } catch (err) {
                notify(err.message || 'Error loading data', 'error');
            } finally {
                setLoading(false);
            }
        };
        fetchInitialData();
    }, [productId, isEditing, notify]);

    const handleChange = (e) => {
        const { name, value, type } = e.target;
        const parsedValue = name === 'categoria_id' ? parseInt(value, 10) :
            type === 'number' ? parseFloat(value) || 0 : value;
        setProductData(prev => ({ ...prev, [name]: parsedValue }));
    };

    const handleFileChange = (e) => {
        const files = Array.from(e.target.files);
        if (visibleImages.length + files.length > 3) {
            notify('Un producto no puede tener más de 3 imágenes en total.', 'error');
            e.target.value = null;
            return;
        }
        setImageFiles(files);
    };

    const handleDeleteExistingImage = (imageUrl) => {
        setImagesToDelete(prev => [...prev, imageUrl]);
        setVisibleImages(prev => prev.filter(img => img !== imageUrl));
    };

    const handleDragEnd = (event) => {
        const { active, over } = event;
        if (active.id !== over.id) {
            setVisibleImages((items) => {
                const oldIndex = items.indexOf(active.id);
                const newIndex = items.indexOf(over.id);
                return arrayMove(items, oldIndex, newIndex);
            });
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        const formData = new FormData();
        for (const key in productData) {
            if (productData[key] !== null && productData[key] !== '') {
                formData.append(key, productData[key]);
            }
        }

        try {
            if (isEditing) {
                if (imagesToDelete.length > 0) {
                    formData.append('images_to_delete', imagesToDelete.join(','));
                }
                if (visibleImages.length > 0) {
                    formData.append('image_order', visibleImages.join(','));
                }
                imageFiles.forEach(file => {
                    formData.append('new_images', file);
                });
                await updateProduct(productId, formData);
            } else {
                if (imageFiles.length === 0) {
                    notify('Debes subir al menos una imagen para crear el producto.', 'error');
                    setLoading(false);
                    return;
                }
                imageFiles.forEach(file => {
                    formData.append('images', file);
                });
                await createProduct(formData);
            }
            notify(`Producto ${isEditing ? 'actualizado' : 'creado'} con éxito!`, 'success');
            navigate('/admin/products');
        } catch (err) {
            const errorMessage = err.response?.data?.detail || 'Ocurrió un error al guardar el producto.';
            notify(errorMessage, 'error');
        } finally {
            setLoading(false);
        }
    };

    if (loading && !categories.length) return <Spinner message="Cargando datos..." />;

    return (
        <div>
            <h1>{isEditing ? 'Editar Producto' : 'Añadir Nuevo Producto'}</h1>
            <form onSubmit={handleSubmit} className="admin-form">
                <div className="form-grid">
                    {Object.keys(productData).map(key => (
                        <div className="form-group" key={key}>
                            <label htmlFor={key}>{key.replace(/_/g, ' ').toUpperCase()}</label>
                            {key === 'categoria_id' ? (
                                <select
                                    id="categoria_id"
                                    name="categoria_id"
                                    value={productData.categoria_id}
                                    onChange={handleChange}
                                    required
                                    style={{ width: '100%', padding: '0.5rem 0', background: 'none', border: 'none', borderBottom: '1px solid #000', fontSize: '1rem' }}
                                >
                                    <option value="" disabled>-- Seleccione una categoría --</option>
                                    {categories.map(cat => (
                                        <option key={cat.id} value={cat.id}>{cat.nombre}</option>
                                    ))}
                                </select>
                            ) : (
                                <input
                                    type={['precio', 'stock'].includes(key) ? 'number' : 'text'}
                                    id={key}
                                    name={key}
                                    value={productData[key]}
                                    onChange={handleChange}
                                    required={!['descripcion', 'material', 'talle', 'color'].includes(key)}
                                />
                            )}
                        </div>
                    ))}
                </div>

                <div className="form-group" style={{ gridColumn: '1 / -1', marginTop: '1rem' }}>
                    <label htmlFor="images">AÑADIR IMÁGENES (hasta 3 en total)</label>
                    <input type="file" id="images" name="images" multiple accept="image/*" onChange={handleFileChange} />

                    {isEditing && (
                        <div style={{ marginTop: '10px' }}>
                            <p>Imágenes actuales (arrastra para reordenar):</p>
                            <DndContext
                                sensors={sensors}
                                collisionDetection={closestCenter}
                                onDragEnd={handleDragEnd}
                            >
                                <SortableContext
                                    items={visibleImages}
                                    strategy={rectSortingStrategy}
                                >
                                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                                        {visibleImages.map(img => (
                                            <SortableImage key={img} id={img} src={img} onRemove={handleDeleteExistingImage} />
                                        ))}
                                    </div>
                                </SortableContext>
                            </DndContext>
                        </div>
                    )}
                </div>

                <button type="submit" className="submit-btn" disabled={loading}>
                    {loading ? 'Guardando...' : 'Guardar Producto'}
                </button>
            </form>
        </div>
    );
};

export default AdminProductFormPage;