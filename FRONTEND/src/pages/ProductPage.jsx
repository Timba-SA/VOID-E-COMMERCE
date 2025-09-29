import React, { useState, useEffect, useContext, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { CartContext } from '../context/CartContext';
import { NotificationContext } from '../context/NotificationContext';
import { getProductById } from '../api/productsApi';
import Spinner from '../components/common/Spinner';

const transformCloudinaryUrl = (url, width) => {
  if (!url || !url.includes('cloudinary')) return url;
  const parts = url.split('/upload/');
  return `${parts[0]}/upload/f_auto,q_auto:best,w_${width}/${parts[1]}`;
};

const getSafeImageUrls = (urls) => {
    if (Array.isArray(urls) && urls.length > 0) {
        return urls;
    }
    return ['/img/placeholder.jpg'];
};

const ProductPage = ({ onOpenCartModal, onSetAddedItem }) => {
    const { productId } = useParams();
    const { addItemToCart } = useContext(CartContext);
    const { notify } = useContext(NotificationContext);

    const [product, setProduct] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // --- ¡NUEVA LÓGICA DE ESTADO! ---
    const [selectedColor, setSelectedColor] = useState(null);
    const [selectedSize, setSelectedSize] = useState(null);

    const [mainImage, setMainImage] = useState('');
    const [allImageUrls, setAllImageUrls] = useState([]);

    useEffect(() => {
        const fetchProductData = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await getProductById(productId);
                if (!data) {
                    throw new Error('Producto no encontrado.');
                }
                setProduct(data);

                const imageUrls = getSafeImageUrls(data.urls_imagenes);
                setAllImageUrls(imageUrls);
                setMainImage(imageUrls[0]);

                if (data.variantes && data.variantes.length > 0) {
                    const firstAvailableVariant = data.variantes.find(v => v.cantidad_en_stock > 0);
                    if (firstAvailableVariant) {
                        const firstColor = firstAvailableVariant.color;
                        setSelectedColor(firstColor);
                        
                        const firstSizeForColor = data.variantes.find(v => v.color === firstColor && v.cantidad_en_stock > 0);
                        if (firstSizeForColor) {
                            setSelectedSize(firstSizeForColor.tamanio);
                        } else {
                            setSelectedSize(null);
                        }
                    } else {
                        setSelectedColor(null);
                        setSelectedSize(null);
                    }
                }
            } catch (err) {
                const errorMessage = err?.response?.data?.detail || err.message || 'No se pudo encontrar el producto.';
                setError(errorMessage);
                notify(errorMessage, 'error');
            } finally {
                setLoading(false);
            }
        };
        fetchProductData();
        window.scrollTo(0, 0);
    }, [productId, notify]);

    // --- LÓGICA PARA FILTRAR VARIANTES ---
    // Obtenemos los colores únicos que tienen stock
    const availableColors = useMemo(() => {
        if (!product?.variantes) return [];
        const colorsWithStock = product.variantes
            .filter(v => v.cantidad_en_stock > 0)
            .map(v => v.color);
        return [...new Set(colorsWithStock)];
    }, [product]);

    // Obtenemos los talles disponibles PARA EL COLOR SELECCIONADO
    const availableSizesForSelectedColor = useMemo(() => {
        if (!product?.variantes || !selectedColor) return [];
        return product.variantes.filter(v => v.color === selectedColor && v.cantidad_en_stock > 0);
    }, [product, selectedColor]);

    const handleColorSelect = (color) => {
        setSelectedColor(color);
        // Al cambiar de color, reseteamos el talle o seleccionamos el primero disponible
        const firstAvailableSize = product.variantes.find(v => v.color === color && v.cantidad_en_stock > 0);
        setSelectedSize(firstAvailableSize ? firstAvailableSize.tamanio : null);
    };

    const handleAddToCart = () => {
        if (!selectedColor || !selectedSize) {
            notify("Please select a color and size.", "error");
            return;
        }

        const selectedVariant = product.variantes.find(
            v => v.tamanio === selectedSize && v.color === selectedColor
        );

        if (!selectedVariant || selectedVariant.cantidad_en_stock <= 0) {
            notify("This option is out of stock.", "error");
            return;
        }

        const itemToAdd = {
            variante_id: selectedVariant.id,
            quantity: 1,
            price: product.precio,
            name: product.nombre,
            image_url: allImageUrls[0] || null,
            size: selectedVariant.tamanio,
            color: selectedVariant.color,
        };
        
        addItemToCart(itemToAdd);
        onSetAddedItem(itemToAdd);
        onOpenCartModal();
    };

    if (loading) return <Spinner message="Loading product..." />;
    if (error) return <div className="error-container" style={{ textAlign: 'center', padding: '5rem' }}><h1>Error: {error}</h1></div>;
    if (!product) return <div style={{ textAlign: 'center', padding: '5rem' }}><h1>Producto no encontrado.</h1></div>;
    
    const isOutOfStock = availableColors.length === 0;
    
    const formatPrice = (price) => {
        if (typeof price !== 'number') {
            return '$--';
        }
        return new Intl.NumberFormat('es-AR', {
          style: 'currency',
          currency: 'ARS',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(price);
    };

    return (
        <main>
            <div className="product-details-container-full">
                <div className="product-images-column" style={{ flexBasis: '45%', flexShrink: 0 }}>
                  <div style={{ maxWidth: '450px', margin: '0 auto' }}>
                    <div className="main-image-container" style={{ marginBottom: '1rem' }}>
                      <img src={transformCloudinaryUrl(mainImage, 600)} alt={product.nombre} style={{ width: '100%', height: 'auto', objectFit: 'contain' }} />
                    </div>
                    {allImageUrls.length > 1 && (
                        <div className="thumbnail-container" style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                          {allImageUrls.map((url, index) => (
                            <div
                              key={index}
                              className="thumbnail-item"
                              onClick={() => setMainImage(url)}
                              style={{
                                cursor: 'pointer',
                                border: mainImage === url ? '2px solid #000' : '2px solid transparent',
                                padding: '2px'
                              }}
                            >
                              <img
                                src={transformCloudinaryUrl(url, 100)}
                                alt={`Thumbnail ${index + 1}`}
                                style={{ width: '80px', height: '80px', objectFit: 'cover' }}
                              />
                            </div>
                          ))}
                        </div>
                    )}
                  </div>
                </div>
                
                <div className="product-info-panel-full" style={{ flexBasis: '55%', paddingLeft: '3rem' }}>
                    <h1 className="product-name">{product.nombre}</h1>
                    <p className="product-price">{formatPrice(product.precio)}</p>
                    
                    {/* --- SELECCIÓN DE COLOR --- */}
                    <div className="product-selector">
                        <p className="selector-label">COLOR: <span>{selectedColor || 'N/A'}</span></p>
                        <div className="selector-buttons">
                            {availableColors.map(color => (
                                <button
                                    key={color}
                                    className={`size-button ${selectedColor === color ? 'active' : ''}`}
                                    onClick={() => handleColorSelect(color)}
                                >
                                    {color}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* --- SELECCIÓN DE TALLE --- */}
                    <div className="product-selector">
                        <p className="selector-label">SIZE: <span>{selectedSize || 'N/A'}</span></p>
                        <div className="selector-buttons">
                            {availableSizesForSelectedColor.map(variant => (
                                <button
                                    key={variant.tamanio}
                                    className={`size-button ${selectedSize === variant.tamanio ? 'active' : ''}`}
                                    onClick={() => setSelectedSize(variant.tamanio)}
                                    disabled={variant.cantidad_en_stock <= 0}
                                >
                                    {variant.tamanio}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="product-description-full">
                        <p>{product.descripcion || "No description available."}</p>
                    </div>
                    
                    <button onClick={handleAddToCart} disabled={isOutOfStock} className="add-to-cart-button">
                        {isOutOfStock ? 'OUT OF STOCK' : 'ADD TO BAG'}
                    </button>
                </div>
            </div>
        </main>
    );
};

export default ProductPage;