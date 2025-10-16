import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getProductById, createProduct, updateProduct } from '../api/productsApi';
import { getCategories } from '../api/categoriesApi';
import { addVariantAPI, deleteVariantAPI } from '../api/adminApi';
import { NotificationContext } from '../context/NotificationContext';
import Spinner from '../components/common/Spinner';
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, useSortable, rectSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

const SortableImage = ({ id, src, onRemove }) => {
    const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id });
    const style = { transform: CSS.Transform.toString(transform), transition, touchAction: 'none' };

    return (
        <div ref={setNodeRef} style={style} {...attributes} {...listeners} className="sortable-image-item">
            <img src={src} alt="preview" />
            <button type="button" onClick={() => onRemove(id)} className="remove-image-btn">×</button>
        </div>
    );
};

const AdminProductFormPage = () => {
    const { t } = useTranslation();
    const { productId } = useParams();
    const navigate = useNavigate();
    const { notify } = useContext(NotificationContext);

    const [productData, setProductData] = useState({
        nombre: '',
        descripcion: '',  // Descripción en español (por compatibilidad)
        descripcion_es: '',  // Descripción explícita en español
        descripcion_en: '',  // Descripción en inglés
        precio: '',
        sku: '',
        categoria_id: '',
        material: '',
    });

    const [variants, setVariants] = useState([]);
    const [newVariant, setNewVariant] = useState({ tamanio: '', color: '', cantidad_en_stock: '' });
    
    const [categories, setCategories] = useState([]);
    const [visibleImages, setVisibleImages] = useState([]);
    const [imagesToDelete, setImagesToDelete] = useState([]);
    const [loading, setLoading] = useState(true);
    const isEditing = Boolean(productId);

    const sensors = useSensors(useSensor(PointerSensor), useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }));

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
                        descripcion_es: productToEdit.descripcion_i18n?.es || productToEdit.descripcion || '',
                        descripcion_en: productToEdit.descripcion_i18n?.en || '',
                        precio: productToEdit.precio || '',
                        sku: productToEdit.sku || '',
                        categoria_id: productToEdit.categoria_id || '',
                        material: productToEdit.material || '',
                    });
                    setVariants(productToEdit.variantes || []);
                    setVisibleImages(productToEdit.urls_imagenes?.map(url => ({ id: url, url })) || []);
                }
            } catch (err) {
                notify(err.message || t('admin_product_form_data_load_error'), 'error');
            } finally {
                setLoading(false);
            }
        };
        fetchInitialData();
    }, [productId, isEditing, notify]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setProductData(prev => ({ ...prev, [name]: value }));
    };
    
    const handleNewVariantChange = (e) => {
        const { name, value } = e.target;
        setNewVariant(prev => ({ ...prev, [name]: value }));
    };

    const handleFileChange = (e) => {
        const files = Array.from(e.target.files);
        if (visibleImages.length + files.length > 3) {
            notify(t('admin_product_form_max_images_error'), 'error');
            e.target.value = null;
            return;
        }

        const newImageObjects = files.map(file => ({
            id: `new-${file.name}-${Date.now()}`,
            url: URL.createObjectURL(file),
            file: file,
        }));

        setVisibleImages(prev => [...prev, ...newImageObjects]);
    };

    const handleDeleteImage = (idToRemove) => {
        const imageToRemove = visibleImages.find(img => img.id === idToRemove);
        if (!imageToRemove) return;

        if (typeof imageToRemove.id === 'string' && !imageToRemove.url.startsWith('blob:')) {
            setImagesToDelete(prev => [...prev, imageToRemove.url]);
        }
        
        setVisibleImages(prev => prev.filter(img => img.id !== idToRemove));
    };

    const handleDragEnd = (event) => {
        const { active, over } = event;
        if (active.id !== over.id) {
            setVisibleImages((items) => {
                const oldIndex = items.findIndex(item => item.id === active.id);
                const newIndex = items.findIndex(item => item.id === over.id);
                return arrayMove(items, oldIndex, newIndex);
            });
        }
    };

    const handleAddVariant = async () => {
        if (!newVariant.tamanio.trim() || !newVariant.color.trim() || !newVariant.cantidad_en_stock) {
            notify(t('admin_product_form_variant_complete_fields_error'), 'error');
            return;
        }
        try {
            const createdVariant = await addVariantAPI(productId, {
                ...newVariant,
                cantidad_en_stock: Number(newVariant.cantidad_en_stock)
            });
            setVariants([...variants, createdVariant]);
            setNewVariant({ tamanio: '', color: '', cantidad_en_stock: '' });
            notify(t('admin_product_form_variant_added_success'), 'success');
        } catch (err) {
            notify(err.detail || t('admin_product_form_variant_create_error'), 'error');
        }
    };

    const handleDeleteVariant = async (variantId) => {
        if (!window.confirm(t('admin_product_form_variant_delete_confirm'))) return;
        try {
            await deleteVariantAPI(variantId);
            setVariants(variants.filter(v => v.id !== variantId));
            notify(t('admin_product_form_variant_deleted_success'), 'success');
        } catch (err) {
            notify(err.detail || t('admin_product_form_variant_delete_error'), 'error');
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        const formData = new FormData();
        
        // Agregamos los campos normales
        Object.keys(productData).forEach(key => {
            // No enviamos descripcion_es y descripcion_en directamente
            if (key !== 'descripcion_es' && key !== 'descripcion_en') {
                formData.append(key, productData[key]);
            }
        });
        
        // Creamos el objeto descripcion_i18n y lo enviamos como JSON
        const descripcionI18n = {
            es: productData.descripcion_es || productData.descripcion || '',
            en: productData.descripcion_en || ''
        };
        formData.append('descripcion_i18n', JSON.stringify(descripcionI18n));
        
        // Mantenemos la descripción legacy en español
        formData.append('descripcion', productData.descripcion_es || productData.descripcion || '');
        
        formData.append('stock', 0);

        const newImageFiles = visibleImages.filter(img => img.file).map(img => img.file);

        try {
            if (isEditing) {
                if (imagesToDelete.length > 0) formData.append('images_to_delete', imagesToDelete.join(','));
                
                const orderedUrls = visibleImages.map(img => img.url).filter(url => !url.startsWith('blob:')).join(',');
                formData.append('image_order', orderedUrls);
                
                newImageFiles.forEach(file => { formData.append('new_images', file); });

                await updateProduct(productId, formData);
                notify(t('admin_product_form_product_updated_success'), 'success');
                navigate('/admin/products');
            } else {
                if (newImageFiles.length === 0) {
                    notify(t('admin_product_form_min_one_image_error'), 'error'); setLoading(false); return;
                }
                newImageFiles.forEach(file => { formData.append('images', file); });
                const createdProduct = await createProduct(formData);
                notify(t('admin_product_form_product_created_success'), 'success');
                navigate(`/admin/products/edit/${createdProduct.id}`);
            }
        } catch (err) {
            notify(err.response?.data?.detail || t('admin_product_form_save_error'), 'error');
            setLoading(false);
        }
    };

    if (loading) return <Spinner message={t('admin_products_loading')} />;

    return (
        <div>
            <Link to="/admin/products" className="back-link">&larr; {t('admin_product_form_back')}</Link>
            <div className="admin-header" style={{ justifyContent: 'center' }}>
                <h1>{isEditing ? t('admin_product_form_edit_title') : t('admin_product_form_add_title')}</h1>
            </div>
            
            <form onSubmit={handleSubmit} className="admin-form">
                <div className="form-section">
                    <h3>{t('admin_product_form_details_title')}</h3>
                    <div className="form-grid">
                         <div className="form-group">
                            <label htmlFor="nombre">{t('admin_product_form_name')}</label>
                            <input type="text" id="nombre" name="nombre" value={productData.nombre} onChange={handleChange} required />
                        </div>
                        <div className="form-group">
                            <label htmlFor="sku">{t('admin_product_form_sku')}</label>
                            <input type="text" id="sku" name="sku" value={productData.sku} onChange={handleChange} required />
                        </div>
                        <div className="form-group">
                            <label htmlFor="precio">{t('admin_product_form_price')}</label>
                            <input type="number" id="precio" name="precio" value={productData.precio} onChange={handleChange} required min="0" step="0.01" />
                        </div>
                        <div className="form-group">
                            <label htmlFor="categoria_id">{t('admin_product_form_category')}</label>
                            <select id="categoria_id" name="categoria_id" value={productData.categoria_id} onChange={handleChange} required>
                                <option value="" disabled>{t('admin_product_form_select_category')}</option>
                                {categories.map(cat => (
                                    <option key={cat.id} value={cat.id}>{cat.nombre}</option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group full-width">
                            <label htmlFor="descripcion_es">{t('admin_product_form_description')} (Español)</label>
                            <textarea id="descripcion_es" name="descripcion_es" value={productData.descripcion_es} onChange={handleChange} rows="4"></textarea>
                        </div>
                        <div className="form-group full-width">
                            <label htmlFor="descripcion_en">{t('admin_product_form_description')} (English)</label>
                            <textarea id="descripcion_en" name="descripcion_en" value={productData.descripcion_en} onChange={handleChange} rows="4"></textarea>
                        </div>
                        <div className="form-group">
                            <label htmlFor="material">{t('admin_product_form_material')}</label>
                            <input type="text" id="material" name="material" value={productData.material} onChange={handleChange} />
                        </div>
                    </div>
                </div>

                <div className="form-section">
                    <h3>{t('admin_product_form_images_title')}</h3>
                    <div className="form-group">
                        <label htmlFor="images" className="file-input-label">{t('admin_product_form_add_images')}</label>
                        <input type="file" id="images" name="images" multiple accept="image/*" onChange={handleFileChange} className="file-input" />
                    </div>
                    
                    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                        <SortableContext items={visibleImages.map(img => img.id)} strategy={rectSortingStrategy}>
                            <div className="image-preview-grid">
                                {visibleImages.map(img => (
                                    <SortableImage key={img.id} id={img.id} src={img.url} onRemove={handleDeleteImage} />
                                ))}
                            </div>
                        </SortableContext>
                    </DndContext>
                </div>

                {isEditing && (
                    <div className="form-section">
                        <h3>{t('admin_product_form_variants_title')}</h3>
                        {variants.length > 0 && (
                            <table className="admin-table variants-table">
                                <thead>
                                    <tr>
                                        <th>{t('admin_product_form_size')}</th>
                                        <th>{t('admin_product_form_color')}</th>
                                        <th>{t('admin_product_form_stock')}</th>
                                        <th>{t('admin_products_table_actions')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {variants.map(variant => (
                                        <tr key={variant.id}>
                                            <td>{variant.tamanio}</td>
                                            <td>{variant.color}</td>
                                            <td>{variant.cantidad_en_stock}</td>
                                            <td className="actions-cell">
                                                <button type="button" className="action-btn delete" onClick={() => handleDeleteVariant(variant.id)}>{t('admin_products_action_delete')}</button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                        
                        <div className="add-variant-form">
                            <h4>{t('admin_product_form_add_variant_title')}</h4>
                            <div className="form-grid">
                                <div className="form-group">
                                    <label>{t('admin_product_form_size')}</label>
                                    <input type="text" name="tamanio" value={newVariant.tamanio} onChange={handleNewVariantChange} placeholder="Ej: M" />
                                </div>
                                <div className="form-group">
                                    <label>{t('admin_product_form_color')}</label>
                                    <input type="text" name="color" value={newVariant.color} onChange={handleNewVariantChange} placeholder="Ej: Negro" />
                                </div>
                                <div className="form-group">
                                    <label>{t('admin_product_form_stock')}</label>
                                    <input type="number" name="cantidad_en_stock" value={newVariant.cantidad_en_stock} onChange={handleNewVariantChange} placeholder="Ej: 50" min="0" />
                                </div>
                                <div className="form-group">
                                    <label>&nbsp;</label>
                                    <button type="button" onClick={handleAddVariant} className="submit-btn secondary">{t('admin_product_form_add_variant_button')}</button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                <button type="submit" className="submit-btn main-submit" disabled={loading}>
                    {loading ? t('admin_product_form_saving_button') : (isEditing ? t('admin_product_form_save_button') : t('admin_product_form_create_button'))}
                </button>
                 {!isEditing && <p className="form-note">{t('admin_product_form_note')}</p>}
            </form>
        </div>
    );
};

export default AdminProductFormPage;